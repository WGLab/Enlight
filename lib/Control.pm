package Control;

use strict;
use warnings;
use CGI qw/:standard/;
use DBI;
use IPC::System::Simple;
use Carp;

sub new
{
    my ($class,%arg)=@_;
    $arg{'maxjobnum'} > 0 or croak ("maxjobnum must be positive!");
    $arg{'maxjobhist'} > 0 or croak ("maxjobhist must be positive!");
    $arg{'wait_time'} > 0 or croak ("wait_time must be positive!");
    $arg{'max_per_ip'} > 0 or croak ("max_per_ip must be positive!");
    $arg{'maxtime'} > 0 or croak ("maxtime must be positive!");
    $arg{'max_run_time'} > 0 or croak ("max running time must be positive!");

    return bless {
	'dbh'		=>$arg{'dbh'} || croak ("No database handle\n"),
	'tablename'	=>$arg{'tablename'} || croak ("No table name\n"),
	'date'		=>$arg{'date'}	|| croak ("No date\n"), 
	'time'		=>$arg{'time'} || croak ("No time\n"),
	'ip'		=>$arg{'ip'}		|| croak ("No IP\n"),
	'query'		=>$arg{'query'}		|| croak ("No query file\n"),
	'access'	=>$arg{'access'} || croak("No access code\n"), 
	'maxjobnum'	=>$arg{'maxjobnum'} || croak("Specify maximum number of jobs\n"),
	'maxjobhist'    =>$arg{'maxjobhist'} || croak ("Specify maximum number of jobs in history"),
	'wait_time'     =>$arg{'wait_time'} || croak ("Specify waiting time before retry"),
	'max_per_ip'    =>$arg{'max_per_ip'} || croak("Specify maximum running jobs per IP"),
	'outdir'        =>$arg{'outdir'} || croak ("No output directory"),
	'maxtime'       =>$arg{'maxtime'} || croak("Specify maximum time for a job to remain in 'running' status"),
	'max_run_time'  =>$arg{'max_run_time'} || croak ("Specify maximum running time for a job"),
	'command'       =>$arg{'command'} || croak("No command for execution"),
	'param'         =>$arg{'param'} || croak("No parameter"),
	'id'		=>undef, #jobID
    }, $class;
}

sub jobControl
{
    #usage: &jobControl()
    #check if there are more than INT jobs running, if not, run $id and return 1 after successful execution, otherwise, check every few sec util successful execution (return 1)
    	my $self=shift;
	my $dbh=$self->{'dbh'};
	my $max=$self->{'maxjobnum'};
	my $id=$self->{'id'};
	my $max_per_ip=$self->{'max_per_ip'};
	my $tablename=$self->{'tablename'};
	my $ip=$self->{'ip'};
	my $wait_time=$self->{'wait_time'};

	while (1)
	{
	    my $sth=$dbh->prepare("SELECT * FROM $tablename WHERE status = 'r'");
	    $sth->execute();
	    my $nrunning=$sth->rows;
	    if ($nrunning >= $max)
	    {
		sleep $wait_time and next;
	    }

	    $sth=$dbh->prepare("SELECT * FROM $tablename WHERE ip = '$ip' AND status = 'r' ");
	    $sth->execute();
	    my $jobsPerIP=$sth->rows;
	    if ($jobsPerIP >= $max_per_ip)
	    {
		sleep $wait_time and next; #wait a moment and check again
	    }

	    #make sure job runs on a first-come first-serve basis
	    $sth=$dbh->prepare("SELECT * FROM $tablename WHERE id < $id AND status = 'q' AND ip='$ip' ");
	    $sth->execute();
	    my $earlyJobs=$sth->rows;
	    if ($earlyJobs>0)
	    {
		sleep $wait_time and next; #wait a moment and check again
	    }

	    #execute
	    $self->jobRun();
	    last;
	}
}

sub jobRun()
{
    #usage: &jobRun()
    #run @command
    my $self=shift;
    my $id=$self->{'id'};
    my $tablename=$self->{'tablename'};
    my @command=@{$self->{'command'}};
    my $dbh=$self->{'dbh'};
    my $query=$self->{'query'};
    my $access=$self->{'access'};
    my $param=$self->{'param'};
    my $outdir=$self->{'outdir'};
    my $max_run_time=$self->{'max_run_time'};

    my $begin_time=time; #seconds from epoch
    my $error;


    chdir $outdir or die "Cannot enter $outdir\n";
    chdir $access or die "Cannot enter $access";

    $dbh->do("UPDATE $tablename SET status = 'r', begin = $begin_time WHERE id = $id");
    #record beginning time, kill long-running process later
    for my $cmd(@command)
    {
	#the following step has been done in process.cgi
	#$cmd=~s/>|<|\*|\?|\[|\]|`|\$|\||;|&|\(|\)|\#|'|"//g; #remove shell metacharacters
	eval {
	    local $SIG{ALRM}=sub { die "Exceeding maxium time ($max_run_time seconds) allowed.\n" };
	    alarm $max_run_time;
	    warn "ENLIGHT RUNNING: $cmd\n";
	    IPC::System::Simple::system("$cmd 1>&2"); #use this to avoid zombies. It dies upon failures
	    alarm 0;
	};
	$error.="CMD:$cmd\nERR:$@\n" and last if $@; #capture eval block message, exit at first error
    }

    chdir $outdir;

    $error? $self->runError($error) : $self->runFinish();

}

sub runFinish
{
    #usage: &runFinish()
    #change job status to 'f', print result page
    my $self=shift;
    my $id=$self->{'id'};
    my $tablename=$self->{'tablename'};
    my $dbh=$self->{'dbh'};
    my $end_time=time;

    $dbh->do("UPDATE $tablename SET status = 'f',end = $end_time WHERE id = $id");
}

sub runError
{
    #usage: $self->runError($msg)
    my $self=shift;
    my $msg=shift;
    my $id=$self->{'id'};
    my $tablename=$self->{'tablename'};
    my $dbh=$self->{'dbh'};

    $dbh->do("UPDATE $tablename SET status = 'e' WHERE id = $id");
    die ("Failed to run.\n$msg");
}

sub jobClean
{
    #usage: $self->jobClean()
    #check if there are more than INT jobs finished, but not deleted from server, if yes, delete the oldest job until there are only INT jobs on server
    my $self=shift;
    my $force=shift;
    my $max=$self->{'maxjobhist'};
    my $tablename=$self->{'tablename'};
    my $dbh=$self->{'dbh'};
    my $outdir=$self->{'outdir'};

    my $check=time;
    #return if $check % 360; #clean at most every 1hr
    my @clean;
    my $sth=$dbh->prepare("SELECT id,access FROM $tablename WHERE (status = 'f' OR status = 'e') ORDER BY id DESC LIMIT $max,18446744073709551615"); #fetch finished jobs, sorted by id,descending
    $sth->execute();
    if ($sth->rows() > $max)
    {
	for my $row ( @{$sth->fetchall_arrayref()} )
	{
	    my ($id, $access)=@{$row};
	    chdir $outdir or die "Cannot enter $outdir\n";
	    push @clean,$id;
	    ! system("rm -rf $access") or die ("Cannot remove $access: $!");
	}
    }
    if ($force)
    {
	#remove queued and running jobs
	$sth=$dbh->prepare("SELECT id,access,status FROM $tablename WHERE (status = 'r' OR status = 'q')"); #fetch finished jobs, sorted by id, ascending
	$sth->execute();
	for my $row ( @{$sth->fetchall_arrayref()} )
	{
	    my ($id, $access,$status)=@{$row};
	    chdir $outdir or die "Cannot enter $outdir\n";
	    push @clean,$id;
	    ! system("rm -rf $access") or die ("Cannot remove $access: $!")
	    							if $status=~/r/;
	}
    }
    map {$dbh->do("UPDATE $tablename SET status = 'c' WHERE id = '$_'")} @clean;

}

sub jobCheck
{
    #usage: $self->jobCheck()
    #check how long job's been running, change job status with running time exceeding threshold
    #this is for unexpected exit (like server crash)
    my $self=shift;
    my $maxtime=$self->{'maxtime'};
    my $tablename=$self->{'tablename'};
    my $dbh=$self->{'dbh'};

    my $current_time=time;
    my $sth=$dbh->prepare("SELECT id,begin FROM $tablename WHERE status = 'r'");
    $sth->execute();

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

sub tablePrepare
{
    my $self=shift;
    my $dbh=$self->{'dbh'};
    my $tablename=$self->{'tablename'};

    my $serverdb_gen="CREATE TABLE IF NOT EXISTS $tablename (id INTEGER PRIMARY KEY AUTO_INCREMENT,date TEXT,time TEXT,ip TEXT,query TEXT,filesize BIGINT UNSIGNED,status TEXT,begin INTEGER UNSIGNED, end INTEGER UNSIGNED,access TEXT,param TEXT)";

    $dbh->do($serverdb_gen);
}
sub jobRegister
{
    #register submission in server database, set job id
    my $self=shift;
    my $dbh=$self->{'dbh'};
    my $tablename=$self->{'tablename'};
    my $outdir=$self->{'outdir'};

    my $access=$self->{'access'};
    my $param=$self->{'param'};
    my $date=$self->{'date'};
    my $time=$self->{'time'};
    my $ip=$self->{'ip'};
    my $query=$self->{'query'};
    my $filesize=-s $query || 0;

    $time=~s/'/"/g;
    $date=~s/'/"/g;
    $ip=~s/'/"/g;
    $query=~s/'/"/g;
    $access=~s/'/"/g;
    $param=~s/'/"/g;

    my $newsub="INSERT INTO $tablename (date, time, ip, query, filesize,status, access, param) VALUES ('$date','$time','$ip','$query',$filesize,'q','$access','$param')";
    $dbh->do($newsub);
    my $id=$dbh->last_insert_id("","",$tablename,"") or die("Cannot find ID of last submitted job\n");
    $self->_setID($id);

    mkdir $outdir or die "$outdir doesn't exist and cannot be created\n" unless -d $outdir;
    chmod 0733,$outdir;
    chdir $outdir or die "Cannot enter $outdir\n";
    mkdir $access or die "$access doesn't exist and cannot be created\n" unless -d $access;
    chmod 0777,$access;
}


sub jobMonitor
{
    my $self=shift;
    my $dbh=shift or die ("No database handle\n");
    my $tablename=shift or die ("No table name\n");

    my $content;
    my $ref=$dbh->selectall_arrayref(
    "SELECT id,status,query,filesize,time,date FROM $tablename WHERE (status = 'r' OR status = 'q' AND filesize>0) ORDER BY status,id");

    $content=th(['jobID','status','filesize','submission time','submission date']);

    for my $row (@{$ref})
    {
	my ($id,$status,$query,$filesize,$time,$date)=@{$row};
	$filesize= scalar ($self->_formatsize($filesize));
	$content.= Tr(
	              td([$id,$status,$filesize,$time,$date]),
	             );
    }

    print header(),
          start_html("Server monitor"),
	  h1("Server status"),
	  table($content),
	  end_html();
}

sub _formatsize 
{
    my $self=shift;
    my $size = shift;
    my $exp = 0;
    my $units = [qw(B KB MB GB TB PB)];
    for (@$units) 
    {
	last if $size < 1024;
	$size /= 1024;
	$exp++;
    }
    return wantarray ? ($size, $units->[$exp]) : sprintf("%.2f %s", $size, $units->[$exp]);
}


sub _setID
{
    #change or set job ID
    my $self=shift;
    my $id=shift;
    $self->{'id'}=$id if $id;
}

sub access
{
    my $self=shift;
    return $self->{'access'};
}

sub outdir
{
    my $self=shift;
    return $self->{'outdir'};
}
1;

=head1 Control

Control: package for managing jobs, reporting errors, and returning results

=head1 SYNOPSIS

use Control;

my $c=Control->new(
    dbh                     =>$dbh,
    tablename               =>"submission",
    maxjobnum               =>$server_conf{'maxjobnum'},
    maxjobhist              =>$server_conf{'maxjobhist'},
    wait_time               =>$server_conf{'waittime'},
    max_per_ip              =>$server_conf{'maxperip'},
    outdir                  =>$server_conf{'outdir'},
    maxtime                 =>$server_conf{'maxtime'},
    max_run_time            =>$server_conf{'max_run_time'},
    command                 =>\@command,
    access                  =>&Utils::rndStr(16,'a'..'z',0..9),
    ip                      =>$ENV{'REMOTE_ADDR'},
    date                    =>$date,
    'time'                  =>$time,
    query                   =>$input,
    param                   =>$param,
);


=head1 AUTHOR

Yunfei Guo

=head1 COPYRIGHT

GPLv3

=cut
