#!/home/yunfeiguo/localperl/bin/perl

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
    $ENV{PERL5LIB}=($ENV{PERL5LIB} ? $ENV{PERL5LIB}:"")."/home/yunfeiguo/localperl/lib/5.18.1:/home/yunfeiguo/localperl/lib/site_perl/5.18.1";
}

chdir File::Spec->catdir($RealBin,"..") or &Utils::error ("Cannot enter installation directory\n"); #go to installation dir for safety

my %server_conf=&Utils::readServConf(File::Spec->catfile($RealBin,"../conf/enlight_server.conf"))
    or &Utils::error ("Reading server configuration file failed!\n");

my $EXAMPLE_LOC="example/exampleinput.txt";
my $EXAMPLE_NAME="exampleinput.txt";
$CGI::POST_MAX = 1024 * 1024 * ($server_conf{'maxupload'}||200);
#all paths should be FULL path
my $log=$server_conf{'serverlog'} || File::Spec->catfile($RealBin,"..","serverlog");
my $admin_email=$server_conf{'admin'} || &Utils::error("No administrator email\n",$log);
my $upload_dir=$server_conf{'tmp'} || "/tmp";
my $dbname=$server_conf{'dbname'} || &Utils::error("No MySQL database name\n",$log,$admin_email);
my $dbuser=$server_conf{'dbuser'} || &Utils::error("No MySQL database user\n",$log,$admin_email);
my $dbpassword=$server_conf{'dbpassword'} || &Utils::error("No MySQL database password\n",$log,$admin_email);
my $generic_table_max=$server_conf{'generic_table_max'} || 20;
#my $private_key=$server_conf{'private_key'} || &Utils::error("No RECAPTCHA private key\n",$log,$admin_email);
my $lz_exe=$server_conf{'locuszoom_exe'} || &Utils::error("No locuszoom executable path\n",$log,$admin_email);
my $anno_dir=$server_conf{'annovar_dir'} || &Utils::error("No ANNOVAR database directory\n",$log,$admin_email);
my $anno_exedir=$server_conf{'annovar_bin'} || &Utils::error("No ANNOVAR executable directory\n",$log,$admin_email);
my $interchr_resolution=$server_conf{'interchr_resolution'} || &Utils::error("no interchr_resolution\n",$log,$admin_email);
my $intrachr_resolution=$server_conf{'intrachr_resolution'} || &Utils::error("no intrachr_resolution\n",$log,$admin_email);
my $interchr_template=$server_conf{'interchr_template'} || &Utils::error("no interchr_template\n",$log,$admin_email);
my $intrachr_template=$server_conf{'intrachr_template'} || &Utils::error("no intrachr_template\n",$log,$admin_email);
my $python_dir=$server_conf{'python_bin'};
my $anno_exe=File::Spec->catfile($RealBin,"..","bin","table_annovar.pl"); #customized version of table_annovar.pl

#use this value with 'region_methodINT' (INT is the index from 0 to 8) to get all region_methods (snp, gene, ...)
#also when single region is specified, 'region_method' is used
my $num_manual_select=$server_conf{'num_manual_region_select'} || &Utils::error("No predefined number of manually specified regions\n",$log,$admin_email);

#read database file settings
my $hg19db=$server_conf{'hg19db'} || &Utils::error("No hg19 database\n",$log,$admin_email);
my $hg18db=$server_conf{'hg18db'} || &Utils::error("No hg18 database\n",$log,$admin_email);
my $hg19mindb=$server_conf{'hg19mindb'} || &Utils::error("No hg19 min database\n",$log,$admin_email);
my $hg18mindb=$server_conf{'hg18mindb'} || &Utils::error("No hg18 min database\n",$log,$admin_email);
my $hg19rs=$server_conf{'hg19rs'} || &Utils::error("No hg19 rsID database\n",$log,$admin_email);
my $hg18rs=$server_conf{'hg18rs'} || &Utils::error("No hg18 rsID database\n",$log,$admin_email);
my $hmmLegend=$server_conf{'hmmLegend'} || &Utils::error("No chromHMM legend\n",$log,$admin_email);

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
my $inputIsExample=1 if $q->param('example_upload');
my $filename=$q->param('query');
my $query_url=$q->param('query_URL');
my $original_uploaded_input;
my $input; #file location of uploaded file
my %custom_table;

my $user_email=$q->param('email'); 
my $file_format=$q->param('qformat');
my $markercol=$q->param('markercol');
my $source_ref_pop=$q->param('source_ref_pop');
my ($ld_source,$ld_ref,$ld_pop)=split(',',$source_ref_pop);

#region specification method
my %region_spec = (
    count	=>	0,
    method	=>	[],#refsnp,refgene,chr
    detail	=>	[],#{flank=>'100kb',refsnp=>'rs10318'},...
);

my $pvalcol=$q->param('pvalcol');
my $ref=$q->param("ref");
my @generic_table=$q->param('generic_table');
my @category_table; #process later, since @generic_table determine how many tracks to be plotted
my $db=($ref eq 'hg19'? $hg19db:$hg18db);
my $mindb=($ref eq 'hg19'? $hg19mindb:$hg18mindb);

my $generic_toggle=1 if (defined $q->param('generic_toggle') && $q->param('generic_toggle') eq 'on');
my $anno_toggle=1 if (defined $q->param('anno_toggle') && $q->param('anno_toggle') eq 'on');
my $ld_toggle=1 if (defined $q->param('ld_toggle') && $q->param('ld_toggle') eq 'on');
my $varAnno=$q->param('varAnno') eq 'NULL'? undef:$q->param('varAnno'); #eQTL db annotation

#option check
&opt_check;

##check upload
&handleUpload;

#again, don't trust user input
&modFileName;

&checkBED(%custom_table) if %custom_table;
&checkHeader($input,$markercol,$pvalcol);

#check and save region specification
&process_region_spec(\%region_spec);

#parameter ok, generate command
my ($param,@unlink);
my @command;


#-------------------------------------------------------------------------------------------
#process annotation tables
#this part has nothing to do with multi-region
if (%custom_table)
{
    #insert custom_table into locuszoom database
    my $tmpdb="locuszoom.tmp.$ref.db";
    my $annodb_exe=File::Spec->catfile($RealBin,"..","bin","annodb_admin");
    my $addbin_exe=File::Spec->catfile($RealBin,"..","bin","formatter")." addbin";
    my $subset_exe=File::Spec->catfile($RealBin,"..","bin","manipulateDB")." subset";
    my $insert_cmd;

    #min_db contains recomb_rate refFlat refsnp_trans snp_pos, it's the basis
    #expand it by tables from db
    #save new db at tmpdb
    #push @command,"$subset_exe $mindb $db $tmpdb @generic_table";
    push @command,"cp $db $tmpdb"; #do not use dump, because it's much slower than copy
    push @unlink,$tmpdb;
    $db=$tmpdb;

    $insert_cmd.=$annodb_exe;
    $insert_cmd.=" -i ".join(',',keys %custom_table);
    $insert_cmd.=" -f ".join(',',values %custom_table);
    $insert_cmd.=" -hg18" if $ref eq 'hg18';
    $insert_cmd.=" -bedinput";
    $insert_cmd.=" $tmpdb";

    push @command,$insert_cmd;

    if ($anno_toggle)
    {
	#when annotation is enabled, and custom tables are uploaded, we'll annotate
	#query files with custom tables in addition to any predefined tables

	#copy mandatory annovar db files
	my @db_name=(@generic_table,"refGene","ALL.sites.2012_04");
	push @db_name,$varAnno if $varAnno; #score or ponly annotation of eqtl and gwas
	push @db_name,"$varAnno.all" if $varAnno; #full annotation of eqtl and gwas
	my @anno_db_file=map { "${ref}_$_.txt" } @db_name;
	push @anno_db_file,"${ref}_ALL.sites.2012_04.txt.idx","${ref}_refGeneMrna.fa";
	my @target=map { File::Spec->catfile($anno_dir,$_) } @anno_db_file;
	map {push @command,"cp $_ ." } @target;
	push @unlink,@anno_db_file; #remove only local version

	for my $name(keys %custom_table)
	{
	    my $file=$custom_table{$name};
	    my $anno_tmp="${ref}_$name.txt";
	    #add BIN column as 1st column is necessary because ANNOVAR will consider this file as one from UCSC genome browser
	    push @command,"$addbin_exe $file $anno_tmp";
	    push @unlink,$file,$anno_tmp;
	}
    }
}

$param.=" legendScale=".(1-0.03*@generic_table);#decrease LD legend as number of generic plots increases
@category_table=grep { /HMM/ } @generic_table;
@generic_table=grep { !/HMM/ } @generic_table;#remove category tracks from generic table
#----------------------------------------------------------------------------------------------------

#convert delimiters to tab
{
    my $tmp="/tmp/$$.2tab";
    if ($file_format ne 'tab')
    {
	push @command, "$RealBin/../bin/formatter delim2tab $file_format $input $tmp";
	$input=$tmp;
    }
}

#do rsID to pos transition if ANNOVAR or varAnnot is requested
#results
if ($anno_toggle || $varAnno)
{
    unless (defined $q->param('avinput') && $q->param('avinput') eq 'on')
    {
	my $tmp="/tmp/$$.rs2avinput";
	push @command, "$RealBin/../bin/formatter rs2avinput $input $tmp $markercol ".($ref eq 'hg18'? $hg18rs:$hg19rs);
	$input=$tmp;
    }
} 

##!!!!!!!!!IMPORTANT!!!!!!!!!
#'input' now becomes 'filename'
{
    $filename=~s/\.csv$/.txt/i;
    push @command,"cp $input $filename";
}

if ($varAnno)
{
    #~/projects/annoenlight/bin/locuszoom --pop EUR --source 1000G_Nov2010 --category wgEncodeBroadHmmHepg2HMM categoryKey=/home/yunfeiguo/projects/annoenlight/conf/chromHMM_legend.txt --generic wgEncodeRegTfbsClusteredV2 --flank 50kb --refsnp rs10318 --pvalcol p --metal rs10318.txt.hg19_multianno.txt --delim tab --db ~/projects/annoenlight/data/database/enlight_hg19.db --build hg19 xyplotCol=GTEX-140712-0019-17897.Brain_Cerebellum.ponly xyplotylab=p --markercol dbSNP135 --plotonly

    #in order to generate XYplot, we have to use p_only file instead
    my $col="${varAnno}"; #this database is solely used for marking variants (exist or not)
    my $anno_table_cmd;
    my $tmp="/tmp/$$".rand($$).".varAnno.tmp";

    $param.=" xyplotCol=$varAnno";
    if($varAnno =~ /chicago/i)
    {
	$param.=" xyplotylab='Score' xyplotlog='NO'";
    } else
    {
	$param.=" xyplotylab='P' xyplotlog='MINUS'";
    }

    $anno_table_cmd.="$anno_exe $filename $anno_dir";
    $anno_table_cmd.=" -protocol $col";
    $anno_table_cmd.=" -operation r";
    $anno_table_cmd.=" -nastring NA";
    $anno_table_cmd.=" -buildver $ref" if $ref;
    $anno_table_cmd.=" -remove";
    $anno_table_cmd.=" -otherinfo";
    $anno_table_cmd.=" -haveheader";

    push @command,$anno_table_cmd;
    push @command,"mv -f $filename.${ref}_multianno.txt $filename";
}

#-------------------------------------------------------------------------------------------
#generate text annotation

if ($anno_toggle)
{
    my %operation;
    my $anno_table_cmd;
    for(@generic_table,keys %custom_table)
    {
	$operation{$_}='r5';
    }
    for (@category_table)
    {
	$operation{$_}='r';
    }
    if($varAnno)
    {
	#eqtl and gwas catalogue full annotation 
	#(beyond score and p) has a suffix .all
	$operation{"${varAnno}.all"}='r';
    }

    $anno_table_cmd.="$anno_exe $filename ";
    $anno_table_cmd.=( %custom_table ? ".":$anno_dir);
    $anno_table_cmd.=" -protocol ".join(',',"refGene","1000g2012apr_all",map {$_} sort keys %operation);
    $anno_table_cmd.=" -operation g,f".(%operation? ",":"").join(',',map {$operation{$_}} sort keys %operation);
    $anno_table_cmd.=" -nastring NA";
    $anno_table_cmd.=" -buildver $ref" if $ref;
    $anno_table_cmd.=" -remove";
    $anno_table_cmd.=" -otherinfo";
    $anno_table_cmd.=" -haveheader";

    push @command,$anno_table_cmd;
}
#all annotations written to .hg1*_multianno file
#------------------------------------------------------------------------------------------

#locuszoom command generation will done multiple times
#depending on user's request
#3 types of region specification: refsnp, refgene, chr/start/end
#3 ways to enter region specification: manual single region/manual multi-region/multi-region hitspec file

#locuszoom command generation is split into two parts: fixed, extensible
{
#fixed, this part has nothing to do with multiple plots
    $param.=" --metal $filename".($anno_toggle?".${ref}_multianno.txt":"");
    $param.=" --build $ref" if $ref;
    $param.=" --markercol $markercol" if $markercol;
    $param.=" --source $ld_source" if $ld_source;
    if (@category_table)
    {
	$param.=" --category ".join(',',@category_table);
	$param.=" categoryKey=$hmmLegend" if -f $hmmLegend;
    }
    $param.=" --generic ".join (',',@generic_table,keys %custom_table) if ($generic_toggle && (@generic_table||%custom_table));
    $param.=" --pop $ld_pop" if $ld_pop;
    $param.=" --pvalcol $pvalcol" if $pvalcol;
    $param.=" --delim tab"; #all delimiters have been converted to TAB
    $param.=" --plotonly";
    $param.=" --db $db";
    #hic interaction data
    if ( $q->param('heatmap_toggle') eq 'on')
    {
	$param.= &getInteractionConf(
	    {   cell	=>	$q->param('interaction_cell_type'),
		type	=>	$q->param('interaction_type'),
		chr     =>	$q->param('interaction_chr'),
	    });
    }
    $param.=" --write-ld-to LD_Rsquare" if $ld_toggle && $q->param('region_multi_single_button') eq 'single'; #write ld for single region mode
#extensible, this part determines how many plots will be generated
    for my $i(0..$region_spec{count}-1)
    {
#generate locuszoom command
	#there are 3 situations: single-region, multi-region, hitspec
	#the first two will be dealt in the same fashion
	my $region_param;
	my $method = $region_spec{method}->[$i];
	my $flank = $region_spec{detail}->[$i]->{flank};
	my $snp = $region_spec{detail}->[$i]->{refsnp};
	my $gene = $region_spec{detail}->[$i]->{refgene};
	my $chr = $region_spec{detail}->[$i]->{chr};
	my $start = $region_spec{detail}->[$i]->{start};
	my $end = $region_spec{detail}->[$i]->{end};
	my $hitspec = $region_spec{detail}->[$i]->{file};
	#4 values in method: hitspec, snp, gene, chr
	if($method eq 'hitspec')
	{
	    $region_param.=" --hitspec $hitspec" if $hitspec;
	} elsif ($method eq 'snp')
	{
	    $region_param.=" --flank ${flank}kb" if $flank;
	    $region_param.=" --refsnp $snp" if $snp;
	} elsif ($method eq 'gene')
	{
	    $region_param.=" --refgene $gene" if $gene;
	    $region_param.=" --flank ${flank}kb" if $flank;
	    $region_param.=" --refsnp $snp" if $snp;
	} elsif ($method eq 'chr')
	{
	    $region_param.=" --chr $chr" if $chr;
	    $region_param.=" --start ".$start*1_000_000 if $start;
	    $region_param.=" --end ".$end*1_000_000 if $end;
	    $region_param.=" --refsnp $snp" if $snp;
	} else
	{
	    &Utils::error("Unrecognized region specification method: $method",$log,$admin_email);
	}

	push @command,"$lz_exe $param $region_param";
    }
}
push @unlink,"ld_cache.db"; #locuszoom cache
#locuszoom --build hg19 --markercol dbSNP135 --source 1000G_Nov2010 --pop EUR --flank 100kb --refsnp rs10318 --category wgEncodeBroadHmmGm12878HMM,wgEncodeBroadHmmH1hescHMM --pvalcol p --metal rs10318.txt  --prefix chrhmm categoryKey=~/projects/annoenlight/data/database/chromHMM_legend.txt --generic wgEncodeUwDnaseCaco2HotspotsRep1,wgEncodeRegTfbsClusteredV2
#remove varanno column
#-------------------------------------------------------------------------------------------
if ($varAnno)
{
    #FIXME!!!!
    #change _existence to ponly column
    my $rmcol=File::Spec->catfile($RealBin,"..","bin","formatter")." rmcol";
    push @command,"$rmcol $filename ${varAnno}";
    push @command,"$rmcol $filename.${ref}_multianno.txt ${varAnno}" if $anno_toggle;
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
    'query'			=>$original_uploaded_input,
    'param'			=>$param,
);

my $base_url=$q->url(-base=>1);
my $result_url=$base_url."/output/".$c->access(); #Don't forget to map /output URL to output dir, or just create 'output' dir inside document root
&Utils::generateFeedback($result_url);

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
    my $fh;
    my @custom_table_fh=$q->upload('custom_table');
    my @custom_table_name=$q->param('custom_table');


    if ($inputIsExample)
    {
#copy example to temp and continue
	my $tmp="/tmp/$$".rand($$).".tmp";
	!system("cp $EXAMPLE_LOC $tmp") or &Utils::error( "Failed to copy example to temp: $!\n",$log,$admin_email);
	$input=$tmp;
	$filename=$EXAMPLE_NAME;
    } elsif ($query_url)
    {
	my $tmp=File::Spec->catfile($upload_dir,"$$".rand($$).".tmp");
	!system("wget -nd --retr-symlinks -r -O $tmp --no-check-certificate \'$query_url\'") or &Utils::error("Failed to get input file via URL: $!\n",$log,$admin_email);
	open $fh,'<',$tmp or &Utils::error( "Failed to read input file via URL: $!\n",$log,$admin_email);
	($filename)= $query_url=~m%.+/(.+)$%;
	$filename=$filename || "input.txt";
	$input=$tmp;
    } else
    {
	$fh=$q->upload('query');
	$input=$q->tmpFileName($filename);
    }

    &Utils::error($q->cgi_error,$log,$admin_email) if ($q->cgi_error);
    &Utils::error("ERROR: No input file\n",$log,$admin_email) unless ($fh or $inputIsExample);

    #make sure all input is gunzipped
    if (&Utils::is_gzip($input))
    {
	$input=&Utils::gunzip($input);
	$filename=~s/\.gz$//;
    }

    $original_uploaded_input=$input;

    #remove empty elements
    @custom_table_name=grep { $_ } @custom_table_name;
    if (@custom_table_name)
    {
	&Utils::error("ERROR: No custom data track\n",$log,$admin_email) unless @custom_table_fh;

	for my $i(0..$#custom_table_fh)
	{
	    my $fh=$custom_table_fh[$i];
	    my $name=$custom_table_name[$i];
	    my $file=File::Spec->catfile($upload_dir,"custom_bed$$".rand($$));
	    #improve later
	    open UPLOAD,'>',$file or &Utils::error("Can't write to $file: $!\n",$log,$admin_email);
	    binmode UPLOAD;
	    while (<$fh>)
	    {
		print UPLOAD;
	    }
	    close UPLOAD;
	    $custom_table{$name}=$file;
	}
	for my $i (keys %custom_table)
	{
	    my $file=$custom_table{$i};
	    if (&Utils::is_gzip($file))
	    {
		delete $custom_table{$i} if $i=~/\.gz$/;
		$i=~s/\.gz$//;
		$custom_table{$i}=&Utils::gunzip($file);
	    }
	}
    }

}
sub checkBED
{
    my %bed=@_;

    for my $i(keys %bed)
    {
	my $file=$bed{$i};
	open IN,'<',$file or &Utils::error("Can't open $file ($i): $!\n",$log,$admin_email);
	while (<IN>)
	{
	    s/[\r\n]+$//;
	    next if /^(track|#|browser|\s)/i; #skip header
	    my @f=split (/\t/,$_,-1);
	    &Utils::error("Expect at least 5 columns in BED\n",$log,$admin_email) if @f<5;
	    &Utils::error("Expect 2nd and 3rd columns are numerical in BED\n",$log,$admin_email) unless $f[1]=~/^\d+$/ && $f[2]=~/^\d+$/;
	    &Utils::error("Expect 5th column is score in BED\n",$log,$admin_email) unless $f[4]=~/^\d+$/;
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
	    &Utils::error("Cannot find <<$_>> in header of $file\n",$log,$admin_email) unless $header=~/ $_|$_ /;
	} elsif ($file_format eq 'comma')
	{
	    &Utils::error("Cannot find <<$_>> in header of $file\n",$log,$admin_email) unless $header=~/,$_|$_,/;
	} elsif ($file_format eq 'whitespace')
	{
	    &Utils::error("Cannot find <<$_>> in header of $file\n",$log,$admin_email) unless $header=~/\s$_|$_\s/;
	} elsif ($file_format eq 'tab')
	{
	    &Utils::error("Cannot find <<$_>> in header of $file\n",$log,$admin_email) unless $header=~/\t$_|$_\t/;
	}else
	{
	    &Utils::error("Unkown delimiter: $file_format\n",$log,$admin_email);
	}
    }
}
sub geneINDB
{
    my $gene=shift;
    my $db=shift;

    $gene=~s/>|<|\*|\?|\[|\]|`|\$|\||;|&|\(|\)|\#|'|"//g; #remove illegal characters
    open IN,'-|',"sqlite3 $db 'select chrom from refFlat where geneName=\"$gene\"' " or
    &Utils::error("Failed to read refFlat: $!\n",$log,$admin_email);

    while (<IN>)
    {
	close IN and return 1 if /^chr([\dXYM]+|mito|mt)/i;
    }
    close IN;
    return undef;
}
sub snpINDB
{
    my $snp=shift;
    my $db=shift;

    $snp=~s/>|<|\*|\?|\[|\]|`|\$|\||;|&|\(|\)|\#|'|"//g; #remove illegal characters
    open IN,'-|',"sqlite3 $db 'select snp from snp_pos where snp=\"$snp\"' " or
    &Utils::error("Failed to read snp_pos: $!\n",$log,$admin_email);

    while (<IN>)
    {
	return 1 if /^$snp\s/;
    }
    return undef;
}
sub individual_region_proc
{
    my $conf = shift;
    my $method=shift;
    my $idx = shift;
    my $detail;

    if ($method eq 'snp')
    {
	my ($flank,$snp)=($q->param('snpflank'.$idx) ,$q->param('refsnp'.$idx));
	$detail = { 
	    flank => $flank ,
	    refsnp => $snp,
	};
	return 0 unless $flank && $snp; #none of required fields can be empty
    } elsif ($method eq 'gene')
    {
	my ($flank,$gene,$snp) = (
	    $q->param('geneflank'.$idx) , 
	    $q->param('refgene'.$idx) , 
	    $q->param('refsnp_for_gene'.$idx));

	$detail = { 
	    flank => $flank,
	    refgene => $gene ,
	    refsnp => $snp ,
	};
	return 0 unless $flank && $gene; #none of required fields can be empty
	&Utils::error ("$gene not FOUND in database (NOTE: gene name is case-sensitive)\n",
	    $log,$admin_email) if ($gene and ! &geneINDB($gene,$db));

    } elsif ($method eq 'chr')
    {
	my ($start,$end,$chr,$snp) = (
	    $q->param('start'.$idx) ,
	    $q->param('end'.$idx) ,
	    $q->param('chr'.$idx) ,
	    $q->param('refsnp_for_chr'.$idx));
	$detail = { 
	    start => $start,
	    end => $end ,
	    chr => $chr ,
	    refsnp => $snp ,
	};
	return 0 unless $start && $end && $chr; #none of required fields can be empty
    } else
    {
	&Utils::error("Unrecognized region specification method: $method\n",$log,$admin_email);
    }

    &Utils::error ($detail->{refsnp}." not FOUND in database (NOTE: snp name is case-sensitive)\n",
	$log,$admin_email) if ($detail->{refsnp} and ! &snpINDB($detail->{refsnp},$db));

    #remove weird char
    for my $i(keys %$detail)
    {
	if (defined $detail->{$i})
	{
	    $detail->{$i} =~ s/[\$ \t\r\n\*\|\?\>\<\'\"\,\;\:\[\]\{\}]//g;
	}
    }
    push @{$conf->{detail}},$detail;
    push @{$conf->{method}},$method;
    return 1; #return TRUE if nothing bad happens
}
sub process_region_spec
{
    my $region_conf_ref = shift;
    #first let's figure out which way does the user enter region specification
    my $single_multi_toggle = $q->param('region_multi_single_button');
    my $multi_region_method = $q->param('multi_region_method');
    #single region?
    if($single_multi_toggle eq 'single') 
    #because this is a toggle button,
    #multi indicates current status of single, vice versa
    {
	$region_conf_ref->{count} = 1;
	#since count=1,we pass empty string as index to individual_region_proc
	my $idx='';
	unless (&individual_region_proc($region_conf_ref,$q->param('region_method'.$idx),$idx))
	{
	    &Utils::error("At least one region must be specified\n",$log,$admin_email);
	}
    } elsif ($single_multi_toggle eq 'multi')
    {
	#manual multi-region?
	if ($multi_region_method eq 'multi_region')
	{
		my $idx=0;
	    for my $i(1..$num_manual_select)
	    {
		if(&individual_region_proc($region_conf_ref,$q->param('region_method'.$idx),$idx))
		{
		    $region_conf_ref->{count}++;
		}
		$idx++;
	    }
	    if($region_conf_ref->{count} == 0)
	    {
		&Utils::error("At least one region must be specified in multi-region specification\n",$log,$admin_email);
	    }
	} elsif ( $multi_region_method eq 'region_file')#HITSPEC file?
	{
	    my $fh=$q->upload('region_file');
	    if (!$fh && $q->cgi_error) 
	    {
		&Utils::error($q->cgi_error,$log,$admin_email);
	    }
	    my $hitspec=$q->tmpFileName($q->param('region_file'));
	    $region_conf_ref->{count} = 1;
	    push @{$region_conf_ref->{method}},"hitspec";
	    push @{$region_conf_ref->{detail}},{file=>$hitspec};
	}
    }
    #report region info
    #
    #&Utils::error("all params: ".join(" ",$q->param),$log,$admin_email);
#    &Utils::error("single or multi?: $single_multi_toggle<br>".
#    "what multi_region method: $multi_region_method<br>".
#    "count?: ".$region_conf_ref->{count}."<br>".
#    join(" ","method:",@{$region_conf_ref->{method}}).
#    join(" ","detail:",map{ join(" ",keys %$_,values %$_) }@{$region_conf_ref->{detail}})
#	,$log,$admin_email);
}
sub opt_check
{
    &Utils::error("Illegal email address\n",$log,$admin_email) if ($user_email && $user_email !~ /[\w\-\.]+\@[\w\-\.]+\.[\w\-\.]+/);
    &Utils::error("Too many generic tracks (max: $generic_table_max)\n",$log,$admin_email) if (@generic_table + (grep {$_} $q->param('custom_table')) ) > $generic_table_max;
    if ( $generic_toggle || $anno_toggle )
    {
	unless (@generic_table || %custom_table)
	{
	    &Utils::error("No annotation data tracks selected or uploaded while generic plot or annotation is enabled\n",$log,$admin_email) 
	}
    }
    &Utils::error("Genome builds don't match ($ref vs $source_ref_pop).\n",$log,$admin_email) unless (lc($ld_ref) eq lc($ref));
    &Utils::error("No marker column\n",$log,$admin_email) unless $markercol;
    &Utils::error("No P value column\n",$log,$admin_email) unless $pvalcol;
    &Utils::error("Only letters, numbers, dashes, underscores are allowed in column name\n",$log,$admin_email) if $markercol=~/[^\w\-]/ or $pvalcol=~/[^\w\-]/;
    &Utils::error ("No genome build or illegal genome build: $ref\n",$log,$admin_email) unless $ref=~/^hg1[89]$/;
    &Utils::error ("Either upload from local, or specify a file via URL. Cannot do both.\n",$log,$admin_email) if ($query_url && $filename);
    &Utils::error ("Illegal characters found in URL: \\,\' not allowed.\n",$log,$admin_email) if ($query_url && $query_url=~/[\\']/);
}

#generate correct parameters for interaction plot
#this function is very specific and should be made more generalizable whenever possible
sub getInteractionConf
{
    my $conf=shift;
    my $interactionfile;
    my $result;
    my $resolution;

    &Utils::error("Chromosome must be specified when interchromosomal interaction is enabled",
	$log,$admin_email) if $conf->{type} eq 'interchromosomal' && !$conf->{chr};
    #intrachr example
    #HIC_gm06690_chr10_chr10_100000_exp.txt.BINname_converted
    #HIC_gm06690_chr10_chr10_100000_exp.txt.BINname_convertedhg19
    #interchr example
    #gm06690_HIC_1000000_exp.hg18.txt
    #gm06690_HIC_1000000_exp.hg18.txthg19
    if($conf->{type} eq 'interchromosomal')
    {
	$interactionfile = $interchr_template;
	$resolution=$interchr_resolution;
	$result .= " --chr2 $conf->{chr}";

    } elsif ($conf->{type} eq 'intrachromosomal')
    {
	$interactionfile = $intrachr_template;
	$resolution=$intrachr_resolution;
	$result .= " --chr2 intrachr"; 
	#m2zfast.py will figure out the correct file to use by replacing TARGETCHR with the chr where refsnp is located
    } else
    {
	&Utils::error("Unrecognized interaction type, only interchromosomal and intrachromosomal allowed",
	    $log,$admin_email);
    }
    for my $i("CELLTYPE","RESOLUTION","TARGETCHR")
    {
	my @match = $interactionfile =~ /$i/g;
	&Utils::error("CELLTYPE,RESOLUTION,TARGETCHR are reserved, not allowed in interchrtemplate or intrachrtemplate",
	    $log,$admin_email) if @match > ($i eq 'TARGETCHR'? 2:1);
    }
    $interactionfile =~ s/CELLTYPE/$conf->{cell}/;
    $interactionfile =~ s/RESOLUTION/$resolution/;
    $interactionfile .= $ref if $ref eq 'hg19';
    $result .= " --interactionfile $interactionfile";
    $result .= " heatmapTitlePlus='cell_line:$conf->{cell}'";
}
