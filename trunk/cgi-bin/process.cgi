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

BEGIN
{
    $ENV{PERL5LIB}="$ENV{PERL5LIB}:/path/to/perllib";
}

chdir File::Spec->catdir($RealBin,"..") or die ("Cannot enter installation directory\n"); #go to installation dir for safety

my %server_conf=&Utils::readServConf("$RealBin/../conf/enlight_server.conf")
    or &Utils::error ("Reading server configuration file failed!\n");

$CGI::POST_MAX = 1024 * 1024 * ($server_conf{'maxupload'}||200);
#all paths should be FULL path
my $log=$server_conf{'serverlog'} || File::Spec->catfile($RealBin,"..","serverlog");
my $admin_email=$server_conf{'admin'} || &Utils::error("No administrator email\n",$log);
my $upload_dir=$server_conf{'tmp'} || "/tmp";
my $dbname=$server_conf{'dbname'} || &Utils::error("No MySQL database name\n",$log,$admin_email);
my $dbuser=$server_conf{'dbuser'} || &Utils::error("No MySQL database user\n",$log,$admin_email);
my $dbpassword=$server_conf{'dbpassword'} || &Utils::error("No MySQL database password\n",$log,$admin_email);
my $generic_table_max=$server_conf{'generic_table_max'} || 10;
#my $private_key=$server_conf{'private_key'} || &Utils::error("No RECAPTCHA private key\n",$log,$admin_email);
my $lz_exe=$server_conf{'locuszoom_exe'} || &Utils::error("No locuszoom executable path\n",$log,$admin_email);
my $anno_dir=$server_conf{'annovar_dir'} || &Utils::error("No ANNOVAR database directory\n",$log,$admin_email);
my $anno_exedir=$server_conf{'annovar_bin'} || &Utils::error("No ANNOVAR executable directory\n",$log,$admin_email);
my $python_dir=$server_conf{'python_bin'};
my $anno_exe=File::Spec->catfile($RealBin,"..","bin","table_annovar.pl"); #customized version of table_annovar.pl
my $hg19db=$server_conf{'hg19db'} || &Utils::error("No hg19 database\n",$log,$admin_email);
my $hg18db=$server_conf{'hg18db'} || &Utils::error("No hg18 database\n",$log,$admin_email);

$ENV{PATH}="$anno_exedir:$ENV{PATH}";
$ENV{PATH}="$python_dir:$ENV{PATH}" if $python_dir;

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

#never trust any data from user input
my $filename=$q->param('query');
my $input; #file location of uploaded file
my %custom_table;

my $user_email=$q->param('email'); 
my $file_format=$q->param('qformat');
my $markercol=$q->param('markercol');
my $source_ref_pop=$q->param('source_ref_pop');
my ($ld_source,$ld_ref,$ld_pop)=split(',',$source_ref_pop);
my $flank=$q->param('snpflank') || $q->param('geneflank');
my $refsnp=$q->param('refsnp');
my $refgene=$q->param('refgene');
my $chr=$q->param('chr');
my $start=$q->param('start');
my $end=$q->param('end');
my $pvalcol=$q->param('pvalcol');
my $ref=$q->param("ref");
my @generic_table=$q->param('generic_table');
my $nastring=$q->param('nastring');
my $db=($ref eq 'hg19'? $hg19db:$hg18db);

my $generic_toggle=1 if (defined $q->param('generic_toggle') && $q->param('generic_toggle') eq 'on');
my $anno_toggle=1 if (defined $q->param('anno_toggle') && $q->param('anno_toggle') eq 'on');

#option check
die ("Illegal email address\n") if ($user_email && $user_email !~ /[\w\-\.]+\@[\w\-\.]+\.[\w\-\.]+/);
die ("Too many generic tracks (max: $generic_table_max)\n") if (@generic_table + (grep {$_} $q->param('custom_table')) ) > $generic_table_max;
if ( $generic_toggle || $anno_toggle )
{
    unless (@generic_table || %custom_table)
    {
	die ("No annotation data tracks selected or uploaded while generic plot or annotation is enabled\n") 
    }
}
die ("Genome builds don't match ($ref vs $source_ref_pop).\n") unless (lc($ld_ref) eq lc($ref));
die ("No marker column\n") unless $markercol;
die ("No P value column\n") unless $pvalcol;
die ("No genome build or illegal genome build: $ref\n") unless $ref=~/^hg1[89]$/;

#check upload
&handleUpload;

#again, don't trust user input
&modFileName;

&checkBED(%custom_table) if %custom_table;
&checkHeader($input,$markercol,$pvalcol);

&Utils::generateFeedback();

#parameter ok, generate command
my ($param,$lz_cmd,$anno_table_cmd,@unlink);
my @command;


#-------------------------------------------------------------------------------------------
if (%custom_table)
{
    #insert custom_table into locuszoom database
    my $tmpdb="locuszoom.tmp.$ref.db";
    my $annodb_exe=File::Spec->catfile($RealBin,"..","bin","annodb_admin");
    my $addbin_exe=File::Spec->catfile($RealBin,"..","bin","formatter")." addbin";
    my $insert_cmd;

    push @command,"cp $db $tmpdb";
    push @unlink,$tmpdb;
    $db=$tmpdb;

    $insert_cmd.=$annodb_exe;
    $insert_cmd.=" -i ".join(',',keys %custom_table);
    $insert_cmd.=" -f ".join(',',values %custom_table);
    $insert_cmd.=" -hg18" if $ref eq 'hg18';
    $insert_cmd.=" $tmpdb";
    push @command,$insert_cmd;

    if ($anno_toggle)
    {
	#copy annovar db files
	my @anno_db_file=map { "${ref}_$_.txt" } (@generic_table,"refGene","ALL.sites.2012_04");
	push @anno_db_file,"${ref}_ALL.sites.2012_04.txt.idx","${ref}_refGeneMrna.fa";
	my @target=map { File::Spec->catfile($anno_dir,$_) } @anno_db_file;
	map {push @command,"cp $_ ." } @target;
	push @unlink,@anno_db_file; #remove only local version

	for my $name(keys %custom_table)
	{
	    my $file=$custom_table{$name};
	    my $anno_tmp="${ref}_$name.txt";
	    #add BIN column as 1st column is necessary as ANNOVAR will consider this file as one from UCSC genome browser
	    push @command,"$addbin_exe $file $anno_tmp";
	    push @unlink,$file,$anno_tmp;
	}
    }
}

#generate locuszoom command
$param.=" --build $ref" if $ref;
$param.=" --markercol $markercol" if $markercol;
$param.=" --source $ld_source" if $ld_source;
$param.=" --generic ".join (',',@generic_table,keys %custom_table) if ($generic_toggle && (@generic_table||%custom_table));
$param.=" --pop $ld_pop" if $ld_pop;
$param.=" --flank ${flank}kb" if $flank;
$param.=" --refsnp $refsnp" if $refsnp;
$param.=" --refgene $refgene" if $refgene;
$param.=" --chr $chr" if $chr;
$param.=" --start ".$start*1000000 if $start; #unit is MB
$param.=" --end ".$end*1000000 if $end;
$param.=" --pvalcol $pvalcol" if $pvalcol;
$param.=" --metal $input" if $input;
$param.=" --delim $file_format" if $file_format;
$param.=" --plotonly";
$param.=" --db $db";

$lz_cmd="$lz_exe $param";

push @command,$lz_cmd;
push @unlink,"ld_cache.db"; #locuszoom cache
#locuszoom --metal rs10318.txt --pval p --refsnp rs10318 --markercol dbSNP135 --source 1000G_Nov2010 --pop EUR --flank 150kb --build hg19 --generic wgEncodeHaibMethyl450Caco2SitesRep1,wgEncodeRegTfbsClusteredV2 --plotonly
#-------------------------------------------------------------------------------------------

#-------------------------------------------------------------------------------------------
if ($anno_toggle)
{
    my $in=$input;

    #formatter should be able to read and write to the same file
    push @command, "$RealBin/../bin/formatter csv2tab $in $filename" and $in=$filename if $file_format eq 'comma';

    unless (defined $q->param('avinput') && $q->param('avinput') eq 'on')
    {
	if ($ref eq 'hg18')
	{
	    push @command, "$RealBin/../bin/formatter rs2avinput $in $filename $markercol $RealBin/../data/database/hg18_snp135_rs.txt";
	} elsif ($ref eq 'hg19')
	{
	    push @command, "$RealBin/../bin/formatter rs2avinput $in $filename $markercol $RealBin/../data/database/hg19_snp135_rs.txt";
	} 
	$in=$filename;
    }

    $anno_table_cmd.="$anno_exe $in . ";
    $anno_table_cmd.=" -protocol ".join(',',"refGene","1000g2012apr_all",@generic_table,keys %custom_table);
    $anno_table_cmd.=" -operation g,f,".join(',',map {'r'} (@generic_table,keys %custom_table));
    $anno_table_cmd.=" -nastring $nastring" if $nastring;
    $anno_table_cmd.=" -buildver $ref" if $ref;
    $anno_table_cmd.=" -remove";
    $anno_table_cmd.=" -otherinfo";
    $anno_table_cmd.=" -colsWanted 5";
    $anno_table_cmd.=" -haveheader";
    push @command,$anno_table_cmd;
}

push @command,"rm -f @unlink" if @unlink;
map {s/>|<|\*|\?|\[|\]|`|\$|\||;|&|\(|\)|\#|'|"//g} @command; #remove insecure char

#-------------------------------------------------------------------------------------------

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
    'tablename'			=>$server_conf{'tablename'},
    'maxjobnum'			=>$server_conf{'maxjobnum'},
    'maxjobhist'		=>$server_conf{'maxjobhist'},
    'wait_time'			=>$server_conf{'waittime'},
    'max_per_ip'		=>$server_conf{'maxperip'},
    'outdir'			=>$server_conf{'outdir'},
    'maxtime'			=>$server_conf{'maxtime'},
    'max_run_time'		=>$server_conf{'max_run_time'},
    'command'			=>\@command,
    'access'			=>&Utils::rndStr(16,'a'..'z',0..9),
    'ip'			=>$ENV{'REMOTE_ADDR'},
    'date'			=>$date,
    'time'			=>$time,
    'query'			=>$input,
    'param'			=>$param,
);

eval {
    $c->tablePrepare(); #make sure the table exists
    $c->jobCheck();
    $c->jobClean();
    $c->jobRegister(); #job ID will be saved with the object
    $c->jobControl(); #job status totally controlled by Control.pm
}; #capture error message rather than just die, since user might have left our website
#We do not care about the return value from Control.pm, it just dies if anything goes wrong
$dbh->disconnect();
my $error=$@ if $@;

#return results
my $base_url=$q->url(-base=>1);
my $result_url=$base_url."/output/".$c->access(); #Don't forget to map /output URL to output dir, or just create 'output' dir inside document root

&Utils::sendEmail({
	'admin'		=>$admin_email,
	'email'		=>$user_email,
	'base_url'	=>$base_url,
	'url'		=>$result_url,
	'subject'	=>'Enlight Result '.$date,
	'error'		=>($error || undef),
    }) if $user_email;

&Utils::error($error,$log,$admin_email) if $error;

&Utils::genResultPage( File::Spec->catdir($c->outdir(),$c->access()),$result_url ); #generate an index.html page with hyperlinks for all files in $access dir
&Utils::showResult($result_url);


################SUBROUTINES############################
sub handleUpload
{
    my $fh=$q->upload('query');
    my @custom_table_fh=$q->upload('custom_table');
    my @custom_table_name=$q->param('custom_table');

    die ($q->cgi_error) if ($q->cgi_error);
    die ("ERROR: No input file\n") unless $fh;
    $input=$q->tmpFileName($filename);

    #remove empty elements
    @custom_table_name=grep { $_ } @custom_table_name;
    if (@custom_table_name)
    {
	die ("ERROR: No custom data track\n") unless @custom_table_fh;

	for my $i(0..$#custom_table_fh)
	{
	    my $fh=$custom_table_fh[$i];
	    my $name=$custom_table_name[$i];
	    my $file=File::Spec->catfile($upload_dir,"custom_bed$$".rand($$));
	    #improve later
	    open UPLOAD,'>',$file or die "Can't write to $file: $!\n";
	    binmode UPLOAD;
	    while (<$fh>)
	    {
		print UPLOAD;
	    }
	    close UPLOAD;
	    $custom_table{$name}=$file;
	}
    }
}
sub checkBED
{
    my %bed=@_;

    for my $i(keys %bed)
    {
	my $file=$bed{$i};
	open IN,'<',$file or die "Can't open $file ($i): $!\n";
	while (<IN>)
	{
	    s/[\r\n]+$//;
	    next if /^(track|#|browser|\s)/i; #skip header
	    my @f=split /\t/,$_;
	    die "Expect at least 5 columns in BED\n" if @f<5;
	    die "Expect 2nd and 3rd columns are numerical in BED\n" unless $f[1]=~/^\d+$/ && $f[2]=~/^\d+$/;
	    die "Expect 5th column is score in BED\n" unless $f[4]=~/^\d+$/;
	}
	close IN;
    }
}
sub modFileName
{
    #$filename will be used in shell command
    for ($filename)
    {
	s/\s+/_/g;
	s/[^\w\.]//g;
    }

    #custom_table names will be used in shell command and sqlite3 command
    for (keys %custom_table)
    {
	my $oldkey=$_;
	s/[\s\-\.]+/_/g;
	s/[^\w]+//g;
	s/^/i/ if /^[\d_]/;
	$custom_table{$_}=$custom_table{$oldkey};
	delete $custom_table{$oldkey};
    }
}
sub checkHeader
{
    my $file=shift;
    my @cols_to_check=@_;
    my $header=`head -n 1 $file`;
    chomp $header;

    for (@cols_to_check)
    {
	s/^[\t ]+|[\t ]+$//;
	if ($file_format eq 'space')
	{
	    die "Cannot find <<$_>> in header of $file\n" unless $header=~/ $_( |$)/;
	} elsif ($file_format eq 'comma')
	{
	    die "Cannot find <<$_>> in header of $file\n" unless $header=~/,$_(,|$)/;
	} elsif ($file_format eq 'whitespace')
	{
	    die "Cannot find <<$_>> in header of $file\n" unless $header=~/\s$_(\s|$)/;
	} else
	{
	    die "Unkown delimiter: $file_format\n";
	}
    }
}
