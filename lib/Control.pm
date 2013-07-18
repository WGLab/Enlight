#!/usr/bin/perl -T

use strict;
use warnings;
use CGI qw/:standard/;
use CGI::Carp qw/fatalsToBrowser/;
use DBI;
use FindBin qw/$RealBin/;
use lib "$RealBin/../lib";
use Utils;
use Captcha::reCAPTCHA;
use IPC::System::Simple;

chdir "$RealBin/../"; #go here for safety

my %server_conf=&Utils::readServConf("$RealBin/../conf/annoenlight_server.conf","$RealBin/..")
    or die ("Reading server configuration file failed!\n"); #no slash after ..
$CGI::POST_MAX = 1024 * 1024 * $server_conf{'maxupload'}; #max upload size
my $upload_dir=$server_conf{'tmp'}; #!!!debug add default values
my $buffersize=$server_conf{'buffersize'};
my $dbname=$server_conf{'dbname'};
my $dbuser=$server_conf{'dbuser'};
my $dbpassword=$server_conf{'dbpassword'};
my $log=$server_conf{'serverlog'};
my $email=$server_conf{'admin'};
my $generic_table_max=$server_conf{'generic_table_max'};
my $maxjobnum=$server_conf{'maxjobnum'};
my $maxjobhist=$server_conf{'maxjobhist'};
my $wait_time=$server_conf{'waittime'};
my $max_per_ip=$server_conf{'maxperip'};
my $outdir=$server_conf{'outdir'};
my $maxtime=$server_conf{'maxtime'};
my $max_run_time=$server_conf{'max_run_time'};
my $private_key=$server_conf{'private_key'};
my $lz_exe=$server_conf{'locuszoom_exe'};


my $time=`date +%H:%M:%S`;
chomp $time;
my $date=`date +%m/%d/%Y`;
chomp $date;

my $q=new CGI;

#check if user is a human
my $c=new Captcha::reCAPTCHA;
my $challenge=$q->param('recaptcha_challenge_field');
my $response=$q->param('recaptcha_response_field');
my $recaptcha_result=$c->check_answer(
    $private_key,$ENV{'REMOTE_ADDR'},
    $challenge,$response
);
&error ("Incorrect verification code.") unless ($recaptcha_result->{is_valid});


#check upload
my $fh=$q->upload('query');

&error($q->cgi_error) if ($q->cgi_error);
&error("ERROR: No uploaded file") unless $fh;

#if filehandle ok, check other paratemeters
#never trust any data from user input!!!!!

my $input=$q->tmpFileName($q->param('query'));
my $file_format=$q->param('qformat');
my $markercol=$q->param('markercol');
my $source_ref_pop=$q->param('source_ref_pop');
my $flank=$q->param('flank');
my $refsnp=$q->param('refsnp');
my $pvalcol=$q->param('pvalcol');
my $generic_toggle=$q->param('generic_toggle');
my $anno_toggle=$q->param('anno_toggle');
my $ref=$q->param("ref");
my @generic_table=$q->param('generic_table');
my $ip=$ENV{'REMOTE_ADDR'};

&error ("Too many generic tracks (max: $generic_table_max)") if @generic_table > $generic_table_max;


my $dsn="DBI:mysql:database=$dbname"; #data source name
my $dbh=DBI->connect($dsn,$dbuser,$dbpassword,{
	RaiseError=>1, #report error via die
    	PrintError=>0, #do not report error via warn
    },) or die "Cannot connect: $DBI::errstr\n";

#job status: (q)ueued, (e)rror, (r)unning, (f)inish, (c)leaned
mkdir $outdir unless -d $outdir;
chdir $outdir;
my $jobid=&jobRegister($dbh);
&jobControl($dbh,$jobid,$maxjobnum);
&jobClean($maxjobhist);
&jobCheck($maxtime);




$dbh->disconnect();

#----------------subroutines--------------------------

sub jobControl
{
    #usage: &jobControl($dbh,$id, INT)
    #check if there are more than INT jobs running, if not, run $id and return 1 after successful execution, otherwise, check every 5s util successful execution (return 1)
    	my $dbh=shift @_;
	my ($id,$max)=@_;
	my $tablename="submission";
	while (1)
	{
	    my $sth=$dbh->prepare("SELECT * FROM $tablename WHERE status = 'r'");
	    $sth->execute();
	    my $nrunning=$sth->rows;

	    if ($nrunning >= $max)
	    {
		sleep $wait_time and next;
	    }

	    $sth=$dbh->prepare("SELECT * FROM $tablename WHERE id = $id");
	    $sth->execute();
	    my $ip=${$sth->fetchrow_hashref}{'ip'};
	    $sth=$dbh->prepare("SELECT * FROM $tablename WHERE ip = '$ip' AND status = 'r' ");
	    $sth->execute();
	    my $jobsperip=$sth->rows;

	    if ($jobsperip >= $max_per_ip)
	    {
		sleep $wait_time and next; #wait a moment and check again
	    }

	    &jobRun($id);
	    last;
	}
}

sub jobRun()
{
    #usage: &jobRun($id)
    my $id=shift;
    my $exe="echo"; #for test only !!!!debug
    #my $exe=$lz_exe;
    #my #anno_table_exe=$table_annovar; #!!!debug add table annovar
    my $tablename="submission";
    my $command;
    my $result;
    my $begin_time=`date +%s`; #seconds from 1970-1-1
    my $msg;


    chomp $begin_time;
    my $sth=$dbh->prepare("SELECT queryname, access, param FROM $tablename WHERE id = $id"); #!!!dbh is global
    $sth->execute();
    my ($query,$access,$param)=$sth->fetchrow_array();
    mkdir $access unless -d $access;
    chdir $access;
    $command="$exe $param";
    $command=~s/>|<|\*|\?|\[|\]|`|\$|\||;|&|\(|\)|\#|\/|'|"//g; #remove shell metacharacters
    $dbh->do("UPDATE $tablename SET status = 'r', begin = $begin_time WHERE id = $id");
    #record beginning time, kill long-running process later
    eval {
	local $SIG{ALRM}=sub { die "Exceeding maxium time ($max_run_time) allowed." };
	alarm $max_run_time;
    	$result=! IPC::System::Simple::system($command); #using IPC::System::Simple's system to avoid zombies
	alarm 0;
    };
    $msg.=$@ if $@; #capture eval block message
    $msg.=$! unless $result; #capture system error message
    $result? &runFinish($id): &runError($id,$msg);
    chdir $outdir;
}

sub runFinish
{
    #usage: &runFinish($id)
    #change job status to 'f', print result page
    my $id=shift;
    my $tablename="submission";
    $dbh->do("UPDATE $tablename SET status = 'f' WHERE id = $id"); #!!!dbh is global
    &showResult($dbh->selectrow_array("SELECT access FROM $tablename WHERE id = $id"));
}

sub showResult
{
    my $access=shift;
    my $result_url=$q->url(-base=>1);
    $result_url.="/$outdir/$access";
    print $q->redirect($result_url);
}

sub runError
{
    my $id=shift;
    my $msg=shift;
    my $tablename="submission";
    $dbh->do("UPDATE $tablename SET status = 'e' WHERE id = $id");
    &error("Failed to run.\n$msg");
}

sub jobClean
{
    #usage: &jobClean(INT)
    #check if there are more than INT jobs finished, but not deleted from server, if yes, delete the oldest job until there are only INT jobs on server
    my $check=`date +%w%M`;
    chomp $check;
    return unless $check eq '001'; #run this at certain time 001 means, sunday, 01 min
    my $max=shift;
    my $tablename="submission";
    my @clean;
    my $sth=$dbh->prepare("SELECT id access FROM $tablename WHERE (status = 'f' OR status = 'e') ORDER BY id"); #fetch finished jobs, sorted by id, ascending
    #!!!debug dbh is global

    $sth->execute();
    if ($sth->rows() > $max)
    {
	for my $row ( @{$sth->fetchall_arrayref()} )
	{
	    my ($id, $access)=@{$row};
	    chdir $outdir;
	    push @clean,$id;
	    ! system("rm -rf $access") or &error ("cannot remove $access: $!");
	}
    }
    $dbh->do("UPDATE $tablename SET status = 'c' WHERE id = '$_'") for @clean;
}

sub jobCheck
{
    #usage: &jobCheck($maxtime)
    #check how long job's been running, change job status with running time exceeding threshold
    #this is for unexpected exit (like server crash)
    my $maxtime=shift;
    my $tablename="submission";
    my $current_time=`date +%s`;
    chomp $current_time;
    my $sth=$dbh->prepare("SELECT id begin FROM $tablename WHERE status = 'r'");

    for my $row (@{$sth->fetchall_arrayref()})
    {
	my ($id,$begin)=@{$row};
	if ( ($current_time-$begin)>$maxtime) 
	{
	    $dbh->do("UPDATE $tablename SET status = 'e' WHERE id = $id");
	    #DO NOT return error message because these jobs are most likely to be dead for external reasons
	}
    }
}

sub jobRegister
{
    #register submission in server database, return job id
    my $dbh=shift;
    my $tablename="submission";
    my $serverdb_gen="CREATE TABLE IF NOT EXISTS $tablename (id INTEGER PRIMARY KEY AUTO_INCREMENT,date TEXT,time TEXT,ip TEXT,queryname TEXT,status TEXT,begin INTEGER UNSIGNED, access TEXT,param TEXT)";
    my $access=&Utils::rndStr(16,'a'..'z',0..9);
    my ($ld_source,$ld_ref,$ld_pop)=split(',',$source_ref_pop);
    &error("Genome builds don't match ($ref vs $source_ref_pop).") unless (lc($ld_ref) eq lc($ref));
    my $param;

    $param.=" --build $ref" if $ref;
    $param.=" --markercol $markercol" if $markercol;
    $param.=" --source $ld_source" if $ld_source;
    $param.=" --generic ".join (',',@generic_table) if @generic_table;
    $param.=" --pop $ld_pop" if $ld_pop;
    $param.=" --metal $$input" if ($upload_dir && $input);
    $param.=" --flank $flank" if $flank;
    $param.=" --refsnp $refsnp" if $refsnp;
    $param.=" --pvalcol $pvalcol" if $pvalcol;
    $param.=" --metal $query" if $query;

    my $newsub="INSERT INTO $tablename (date, time, ip, queryname, status, access, param) VALUES ('$date','$time','$ip','$query','q','$access','$param')";
    #!!!!debug consider quote_identifier, quote methods for SQL statement
    $dbh->do($serverdb_gen);
    $dbh->do($newsub);
    my $id=$dbh->last_insert_id("","",$tablename,"") or &error("Cannot find ID of last submitted job");
    return $id;
}


sub error
{
    #usage: &error("message")
    #generate a HTML webpage displaying error message, log error and exit
    my $msg=shift;
    open ERR,'>',$log or die "Cannot open log file\n";
    my $output=$q->header;
    $output .=$q->start_html(-title=>'AnnoEnlight Server ERORR');
    $output .=$q->p($msg);
    $output .=$q->p("Please contact $email");
    $output .=$q->end_html;
    my $timestamp=`date`;
    chomp $timestamp;
    print ERR "$timestamp\t$msg\n";
    print $output;
    exit 0;
}
