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

chdir File::Spec->catdir($RealBin,"..") or die ("Cannot enter installation directory\n"); #go to installation dir for safety

my %server_conf=&Utils::readServConf("$RealBin/../conf/enlight_server.conf")
    or &Utils::error ("Reading server configuration file failed!\n");

$CGI::POST_MAX = 1024 * 1024 * ($server_conf{'maxupload'}||200);
#all paths should be FULL path
my $log=$server_conf{'serverlog'} || File::Spec->catfile($RealBin,"../serverlog");
my $admin_email=$server_conf{'admin'} || &Utils::error("No administrator email\n",$log);
my $upload_dir=$server_conf{'tmp'} || "/tmp";
my $dbname=$server_conf{'dbname'} || &Utils::error("No MySQL database name\n",$log,$admin_email);
my $dbuser=$server_conf{'dbuser'} || &Utils::error("No MySQL database user\n",$log,$admin_email);
my $dbpassword=$server_conf{'dbpassword'} || &Utils::error("No MySQL database password\n",$log,$admin_email);
my $generic_table_max=$server_conf{'generic_table_max'} || 10;
#my $private_key=$server_conf{'private_key'} || &Utils::error("No RECAPTCHA private key\n",$log,$admin_email);
my $lz_exe=$server_conf{'locuszoom_exe'} || &Utils::error("No locuszoom executable path\n",$log,$admin_email);
my $anno_exe=$server_conf{'annotable_exe'} || &Utils::error("No table_annovar executable path\n",$log,$admin_email);
my $anno_dir=$server_conf{'annovar_dir'} || &Utils::error("No ANNOVAR database directory\n",$log,$admin_email);

my $time=`date +%H:%M:%S`;
chomp $time;
my $date=`date +%m/%d/%Y`;
chomp $date;

my $q=new CGI;

##check if user is a human
#die ("Incorrect verification code.\n") unless 
#	&Utils::humanCheck(
#	    $private_key,$q->param('recaptcha_challenge_field'),$q->param('recaptcha_response_field') 
#	);

#check upload
my $fh=$q->upload('query');

die ($q->cgi_error) if ($q->cgi_error);
die ("ERROR: No uploaded file\n") unless $fh;

#never trust any data from user input

my $user_email=$q->param('email'); 
my $filename=$q->param('query');
my $input=$q->tmpFileName($filename);

my $file_format=$q->param('qformat');
my $markercol=$q->param('markercol');
my $source_ref_pop=$q->param('source_ref_pop');
my ($ld_source,$ld_ref,$ld_pop)=split(',',$source_ref_pop);
my $flank=$q->param('flank');
my $refsnp=$q->param('refsnp');
my $pvalcol=$q->param('pvalcol');
my $ref=$q->param("ref");
my @generic_table=$q->param('generic_table');
my $nastring=$q->param('nastring');

my $generic_toggle=1 if (defined $q->param('generic_toggle') && $q->param('generic_toggle') eq 'on');
my $anno_toggle=1 if (defined $q->param('anno_toggle') && $q->param('anno_toggle') eq 'on');

#option check
die ("Illegal email address\n") if ($user_email && $user_email !~ /.+\@.+\..+/);
die ("Too many generic tracks (max: $generic_table_max)\n") if @generic_table > $generic_table_max;
die ("No generic tracks selected\n") if ( ($generic_toggle || $anno_toggle) && (! @generic_table) );
die ("Genome builds don't match ($ref vs $source_ref_pop).\n") unless (lc($ld_ref) eq lc($ref));
die ("No marker column\n") unless $markercol;
die ("No genome build\n") unless $ref;

&Utils::generateFeedback();

my $status_tmp=localtime."$$.tmp";
my $input_tmp=localtime."$$.input.tmp";
system("cat $input > $input_tmp") and die "Cannot write to $input_tmp: $!\n";
open OUT,'>',$status_tmp or die "Cannot open $status_tmp: $!\n";
$q->save(\*OUT);
close OUT;
system(File::Spec->catfile($RealBin,"process2.cgi")." $status_tmp $input_tmp &"); #run command generation and execution in background, such that a confirmation page can show up before hand.
