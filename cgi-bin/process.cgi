#!/usr/bin/perl -T

use strict;
use warnings;
use CGI::Pretty;
use CGI::Carp qw/fatalsToBrowser/;
use DBI;
use FindBin qw/$RealBin/;
use lib "$RealBin/../lib";
use Utils;
use Captcha::reCAPTCHA;


my %server_conf=&Utils::readServConf("$RealBin/../conf/annoenlight_server.conf","$RealBin/..")
    or die "Reading server configuration file failed!\n"; #no slash after ..
$CGI::POST_MAX = 1024 * 1024 * $server_conf{'maxupload'}; #max upload size
my $upload_dir=$server_conf{'tmp'};
my $buffersize=$server_conf{'buffersize'};
my $dbname=$server_conf{'dbname'};
my $dbuser=$server_conf{'dbuser'};
my $dbpassword=$server_conf{'dbpassword'};
my $log=$server_conf{'serverlog'};
my $email=$server_conf{'admin'};
my $generic_table_max=$server_conf{'generic_table_max'};
my $maxjobnum=$server_conf{'maxjobnum'};
my $maxjobhist=$sever_conf{'maxjobhist'};

my $time=`date +%H:%M:%S`;
chomp $time;
my $date=`date +%m/%d/%y`;
chomp $time;

my $q=new CGI::Pretty;

#check if user is a human
my $c=new Captcha::reCAPTCHA;
my $challenge=$q->param('recaptcha_challenge_field');
my $response=$q->param('recaptcha_response_field');
my $recaptcha_result=$c->check_answer(
    "RECAPTCHA_PRIVATE_KEY",$ENV{'REMOTE_ADDR'},
    $challenge,$response
);
if ($recaptcha_result->{is_valid})
{
    1;
} else
{
    &error ("Incorrect verification code.");
}

my $fh=$q->upload('query');

#handling filehandle error
if ($q->cgi_error)
{
    &error($q->cgi_error);
} 
if (!$fh)
{

    &error("ERROR: No uploaded file");
}

#if filehandle ok, check other paratemeters

my $input=$param('query');
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
my $securityCode=$q->param('security_code');
&error ("Too many generic tracks") if @generic_table > $generic_table_max;
&error ("Incorrect security code, you should type \'$dateSecurity\'.") if $securityCode ne $dateSecurity; #use day number as security code

#debug consider DoS attack

my $dsn="DBI:mysql:database=$dbname";
my $dbh=DBI->connect($dsn,$dbuser,$dbpassword,{
	RaiseError=>1,
    	PrintError=>0,
    },) or die "Cannot connect: $DBI::errstr\n";

#job status: (q)ueue, (e)rror, (r)unning, (f)inish
my $job=&jobRegister($dbh);
&jobRun($job,$maxjobnum) and &jobReturn($job);
&jobClean($maxjobhist);

while(read($fh,$buffer,$buffersize))
{
    print $buffer;
}

print $q->header;
print $q->start_html;
$q->param,$q->end_html;





$dbh->disconnect();
#----------------subroutines--------------------------

sub jobRun
{
    #usage: &jobRun($dbh,$id, INT)
    #check if there are more than INT jobs running, if not, run $id and return 1 after successful execution, otherwise, check every 5s util successful execution (return 1)
	my ($dbh,$id,$max)=@_;
}

sub jobReturn
{
    #usage: &jobReturn($id)
    #return finished results, a pdf and annotation table(optional)
}

sub jobClean
{
    #usage: &jobClean(INT)
    #check if there are more than INT jobs finished, but not deleted from server, if yes, delete the oldest job until there are only INT jobs on server

}

sub jobRegister
{
    #register submission in server database, return job id
    my $dbh=shift;
	my $tablename="submission";
	my $serverdb_gen="CREATE TABLE IF NOT EXISTS $tablename (id INTEGER PRIMARY KEY AUTO_INCREMENT,date TEXT,time TEXT,ip TEXT,queryname TEXT,status TEXT,access TEXT,param TEXT)";
	my $access=&rndStr(16,'a'..'z',0..9);
	my ($ld_source,$ld_ref,$ld_pop)=split(',',$source_ref_pop);
	&error("Genome builds don't match ($ref vs $source_ref_pop).") unless $source_ref_pop =~ /$ref/i;
	my $param;
	$param.="--build $ref" if $ref;
	$param.=" --markercol $markercol" if $markercol;
	$param.=" --source $ld_source" if $ld_source;
	$param.=" --generic ",join (',',@generic_table) if @generic_table;
	$param.=" --pop $ld_pop" if $ld_pop;
	$param.=" --metal $upload_dir/$input" if ($upload_dir && $input);
	$param.=" --flank $flank" if $flank;
	$param.=" --refsnp $refsnp" if $refsnp;
	$param.=" --pvalcol $pvalcol" if $pvalcol;

	my $newsub="INSERT INTO $tablename (date, time, ip, queryname, status, access, param) VALUES ('$date','$time','$ip','$query','q','$access','$param')";
	$dbh->do($serverdb_gen);
	$dbh->do($newsub);
	my $id=$dbh->last_insert_id("","",$tablename,"") or &error("Cannot find ID of last submitted ID");
	return $id;
}


sub rndStr
{
    #usage: &rndStr(INT,@stringOfchar)
    #output random string of length INT consisting of characters from @stringOfchar
    join '',@_[ map {rand @_} 1 .. shift ];
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
