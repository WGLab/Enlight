#!/usr/bin/env perl

use strict;
use warnings;
use CGI qw/:standard/;
use CGI::Carp qw/fatalsToBrowser/;
use DBI;
use FindBin qw/$RealBin/;
use File::Spec;
use lib "$RealBin/../lib";
use Utils;
use Control;

my %op=( #!!!debug: incomplete list; also consider all possible encode data tracks
    refGene=>'g',
    phastConsElements44way=>'r',
    genomicSuperDups=>'r',
    esp6500si_all=>'f',
    '1000g2012apr_all'=>'f',
    snp135=>'f',
    avsift=>'f',
    ljb_all=>'f', 
);

chdir "$RealBin/../" or die ("Cannot enter installation directory\n"); #go to installation dir for safety

my %server_conf=&Utils::readServConf("$RealBin/../conf/enlight_server.conf")
    or &Utils::error ("Reading server configuration file failed!\n");

$CGI::POST_MAX = 1024 * 1024 * $server_conf{'maxupload'};
#all paths should be FULL path
my $log=$server_conf{'serverlog'} || "serverlog";
my $admin_email=$server_conf{'admin'} || &Utils::error("No administrator email\n",$log);
my $upload_dir=$server_conf{'tmp'} || "/tmp";
my $dbname=$server_conf{'dbname'} || &Utils::error("No MySQL database name\n",$log,$admin_email);
my $dbuser=$server_conf{'dbuser'} || &Utils::error("No MySQL database user\n",$log,$admin_email);
my $dbpassword=$server_conf{'dbpassword'} || &Utils::error("No MySQL database password\n",$log,$admin_email);
my $generic_table_max=$server_conf{'generic_table_max'} || 10;
my $private_key=$server_conf{'private_key'} || &Utils::error("No RECAPTCHA private key\n",$log,$admin_email);
my $lz_exe=$server_conf{'locuszoom_exe'} || &Utils::error("No locuszoom executable path\n",$log,$admin_email);
my $anno_exe=$server_conf{'annotable_exe'} || &Utils::error("No table_annovar executable path\n",$log,$admin_email);

my $time=`date +%H:%M:%S`;
chomp $time;
my $date=`date +%m/%d/%Y`;
chomp $date;

my $q=new CGI;

#check if user is a human
die ("Incorrect verification code.\n") unless 
	&Utils::humanCheck(
	    $private_key,$q->param('recaptcha_challenge_field'),$q->param('recaptcha_response_field') 
	);

#check upload
my $fh=$q->upload('query');

die ($q->cgi_error) if ($q->cgi_error);
die ("ERROR: No uploaded file\n") unless $fh;

#if filehandle ok, check other paratemeters
#never trust any data from user input

my $user_email=$q->param('email');
my $input=$q->tmpFileName($q->param('query'));

my $file_format=$q->param('qformat');
my $markercol=$q->param('markercol');
my $source_ref_pop=$q->param('source_ref_pop');
my ($ld_source,$ld_ref,$ld_pop)=split(',',$source_ref_pop);
my $flank=$q->param('flank');
my $refsnp=$q->param('refsnp');
my $pvalcol=$q->param('pvalcol');
my $ref=$q->param("ref");
my @generic_table=$q->param('generic_table');

my $generic_toggle=$q->param('generic_toggle');
my $anno_toggle=$q->param('anno_toggle');

die ("Too many generic tracks (max: $generic_table_max)\n") 
	if @generic_table > $generic_table_max;


die ("Genome builds don't match ($ref vs $source_ref_pop).\n") unless (lc($ld_ref) eq lc($ref));

#parameter ok, generate command
my ($param,$lz_cmd,$anno_table_cmd);
my @command;

$param.=" --build $ref" if $ref;
$param.=" --markercol $markercol" if $markercol;
$param.=" --source $ld_source" if $ld_source;
$param.=" --generic ".join (',',@generic_table) if $generic_toggle && @generic_table;
$param.=" --pop $ld_pop" if $ld_pop;
$param.=" --metal $input" if ($upload_dir && $input);
$param.=" --flank $flank" if $flank;
$param.=" --refsnp $refsnp" if $refsnp;
$param.=" --pvalcol $pvalcol" if $pvalcol;
$param.=" --metal $input" if $input;

&Utils::generateFeedback();

# !!!debug the command is incorrect and needs more arguments
#$lz_cmd="$lz_exe $param";
$lz_cmd="echo 'locuszoom program'> lz.txt";
#/home/username/locuszoom-encode-beta/bin/locuszoom --build hg19 --markercol dbSNP135 --source 1000G_Nov2010 --pop EUR --metal tab_Metal_file.txt --flank 150kb --refsnp rsSNP --pvalcol ccfr_p --generic ENCODEtable1,ENCODEtable2
#$anno_table_cmd="$anno_exe $input $anno_dir -protocol ".join(',',@generic_table)." -operation ".map {$op{$_}} @generic_table."-nastring ".$q->param('NAstring');
$anno_table_cmd="echo 'table_annovar example' > anno.txt";
#table_annovar.pl ex1.human humandb/ -protocol refGene,phastConsElements44way,genomicSuperDups,esp6500si_all,1000g2012apr_all,snp135,avsift,ljb_all -operation g,r,r,f,f,f,f,f -nastring NA

push @command,$lz_cmd;
push @command,$anno_table_cmd if $anno_toggle;


#prepare database, it records job status
#job status: (q)ueued, (e)rror, (r)unning, (f)inish, (c)leaned
my $dsn="DBI:mysql:database=$dbname"; #data source name
my $dbh=DBI->connect($dsn,$dbuser,$dbpassword,{
	RaiseError=>1, #report error via die
    	PrintError=>0, #do not report error via warn
    },) or &Utils::error( "Cannot connect: $DBI::errstr\n",$log,$admin_email);


#turn control to Control.pm
my $c=Control->new(
    	'dbh'			=>$dbh,
	'tablename'		=>$server_conf{'tablename'},
	'maxjobnum'		=>$server_conf{'maxjobnum'},
	'maxjobhist'		=>$server_conf{'maxjobhist'},
	'wait_time'		=>$server_conf{'waittime'},
	'max_per_ip'		=>$server_conf{'maxperip'},
	'outdir'		=>$server_conf{'outdir'},
	'maxtime'		=>$server_conf{'maxtime'},
	'max_run_time'		=>$server_conf{'max_run_time'},
	'command'		=>\@command,
	'access'		=>&Utils::rndStr(16,'a'..'z',0..9),
	'ip'			=>$ENV{'REMOTE_ADDR'},
	'date'			=>$date,
	'time'			=>$time,
	'query'			=>$input,
	'param'			=>$param,
);

eval {
$c->jobRegister(); #job ID will be saved with the object
$c->jobControl(); #job status totally controlled by Control.pm
$c->jobClean();
$c->jobCheck();
}; #capture error message
#We do not care about the return value from Control.pm, it just dies if anything goes wrong
$dbh->disconnect();

my $base_url=$q->url(-base=>1);
my $result_url=$base_url."/output/".$c->access(); #Don't forget to map /output URL to output dir

&Utils::sendEmail({
	'admin'		=>$admin_email,
	'email'		=>$user_email,
	'base_url'	=>$base_url,
	'url'		=>$result_url,
	'subject'	=>'Enlight Result',
	'error'		=>$@,
    }) if $user_email;

&Utils::error($@,$log,$admin_email) if $@;

&Utils::genResultPage( File::Spec->catdir($c->outdir(),$c->access()),$result_url ); #generate an index.html page with hyperlinks for all files in $access dir
&Utils::showResult($result_url);
