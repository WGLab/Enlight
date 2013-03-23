#!/usr/bin/perl -w
use strict;
#use Carp;	#there is no need to use Carp, since we will use the Carp defined in the CGI.pm module.
#use CGI qw(:standard);
use CGI;
use CGI::Carp qw(fatalsToBrowser);
$CGI::POST_MAX = 10240 * 10240 *2;

#define global variables
our $CARETAKER = "xchang\@usc.edu";
our $SERVER_DIRECTORY = "/var/www/html/annovar-server/exec";
our $BIN_DIRECTORY = "${SERVER_DIRECTORY}/bin";
our $WORK_DIRECTORY = "${SERVER_DIRECTORY}/work";
our $SUBMISSION_ID_FILENAME = "${WORK_DIRECTORY}/submission_id"; #file stores the submission id

##########################################################################

my $q = new CGI;

#THE FOLLOWING LINE IS REQUIRED FOR ANY OTHER OUTPUT SUCH AS ERROR OUTPUT FOR FEEDBACK OUTPUT
print $q->header ("text/html");
my $cgi_error = $q->cgi_error;
if ($cgi_error) {
	if ($cgi_error eq "413 Request entity too large") {
		display_error ("Unable to process the information you supplied: $cgi_error! wANNOVAR can not handle files over 200Mb (gz/zip is okay), please download ANNOVAR to perform your analysis", $CARETAKER);
	} else {
		display_error ("Unable to process the information you supplied: $cgi_error!", $CARETAKER);
	}
}

#parse the web form at <http://annovar.usc.edu>
my $ip = $q->param('ip');
my $host = $q->param('host');
&check_ip();
my $sample_id = $q->param('sample_id') or display_error ("Please enter the sample identifier", $CARETAKER);
my $reply_email = $q->param('reply_email') or display_error ("Please enter your email address to receive results", $CARETAKER);;
unless ($reply_email =~ /^(\w|\-|\_|\.)+\@((\w|\-|\_)+\.)+[a-zA-Z]{2,}$/) {
display_error("Please enter a valid email address", $CARETAKER);
};
my $ref_genome = $q->param('ref_genome') or display_error ("Please select a reference genome", $CARETAKER);
my $input_fmt = $q->param('input_fmt') or display_error ("Please select an input format", $CARETAKER);
my $input_model = $q->param('input_model') or display_error ("Please select a disease model", $CARETAKER);
my $input_gene = $q->param('input_gene') or display_error ("Please select a gene definition", $CARETAKER);
my $dbsnp_ver = ($ref_genome eq "hg19") ? "135":"132";
if ($q->param('dbsnp_model')) {
	$dbsnp_ver = $q->param('dbsnp_model');
}
my $disease = "recessive";
if ($q->param('disease_model')) {
	$disease = $q->param('disease_model');
}    
my $vcf_dp = $q->param('vcf_dp') and ($input_fmt ne "vcf4") and display_error ("Depth threshold is for VCF file only!", $CARETAKER); 
my $vcf_qd = $q->param('vcf_qd') and ($input_fmt ne "vcf4") and display_error ("Quality threshold is for VCF file only!", $CARETAKER); 
my $maf_value = $q->param('maf_value');
unless (($maf_value <= 0.5) and ($maf_value >=0)) {
display_error("MAF value should less than 0.5 and great than 0",$CARETAKER);
}
my @step = $q->param('step') and ($input_model ne "custom") and display_error ("Custom variants reduction pipeline is activated only when custom filtering is selected!", $CARETAKER); 
if ($input_model eq "custom" and not defined(@step)) {
display_error ("Please select a filtering step", $CARETAKER);
}
my %step_des = (
        coding=> "nonsyn_splicing",
        mce18=> "phastConsElements44way",
        mce19=> "phastConsElements46way",
        segdup=> "genomicSuperDups",
        kg18=>"1000g2010jul_ceu,1000g2010jul_jptchb,1000g2010jul_yri",
        kg19=>"1000g2012feb_all",
        dbsnp=>"snp".$dbsnp_ver,
        esp6500=>"esp6500si",
        sift=>"ljb_sift",
        pp2=>"ljb_pp2",
	cg46=>"cg46",
        control=>"control",
);
my %step_s = (
	coding=> "nonsyn_splicing",
	mce18=> "phastConsElements44way",
	mce19=> "phastConsElements46way",
	segdup=> "genomicSuperDups",
	kg18=>"1000g2010jul_ceu,1000g2010jul_jptchb,1000g2010jul_yri",
	kg19=>"1000g2012feb_all", 
	dbsnp=>"snp".$dbsnp_ver."NonFlagged",
	esp6500=>"esp6500si_ea,esp6500si_aa",
	sift=>"ljb_sift",
	pp2=>"ljb_pp2",
	cg46=>"cg46",
	control=>"generic",
);
my %step_p = (
	coding=> "g",
	mce18=> "r",
	mce19=> "r",
	segdup=> "rr",
	kg18=>"f,f,f",
	kg19=>"f", 
	dbsnp=>"f",
	esp6500=>"f,f",
	sift=>"f",
	pp2=>"f",
	cg46=>"f",
	control=>"f",
);#g,r,r,f,f,f,f,f,f,f,f,f,m

my @step1;
my @step2;
my @step3;

my $control_selected;
foreach (@step) {
	if ($_ eq "1000g") {
		$_ = ($ref_genome eq "hg18") ? 'kg18' : 'kg19';
	}
	if ($_ eq "mce") {
		$_ = ($ref_genome eq "hg18") ? 'mce18' : 'mce19';
	}
	if ($_ eq 'control') {
		$control_selected = 1;
	}
	push @step1,$step_s{$_};
	push @step2,$step_p{$_};
	push @step3,$step_des{$_};
}

my $step_fs=join ",",@step1;
   $step_fs = $step_fs.",".$disease;
my $step_fp=join ",",@step2;
   $step_fp = $step_fp.",m";
my $step_org = join ",",@step3;

$reply_email ||= "none";

my $variant_call = $q->param('variant_call');  ###change the corresponded name in index.html
my $variant_call_fh;
my $paste_variant = $q->param('paste_variant');

if ($variant_call) {
	$variant_call_fh = $q->upload ('variant_call');
} else {
	$paste_variant or display_error("You must either upload a variant call file or input a list of variant calls!", $CARETAKER);
}

##advanced control sample option
my $control_call = $q->param('control_call');  ###change the corresponded name in index.html
my $control_call_fh;
my $paste_control = $q->param('paste_control');

if ($control_call) {
	if (not $control_selected) {
		display_error("\"not in controls\" must be selected when a variant file on controls is uploaded", $CARETAKER);
	}	
	$control_call_fh = $q->upload ('control_call');
}
else {
	if ($control_selected) {
		display_error("You must upload a variant file on controls when \"not in controls\"", $CARETAKER);
	}
}

my $submission_time = scalar (localtime);
my $submission_id;
my $warning_message = '';
my $weblink;

prepareWorkDirectory ();
generateFeedback ($submission_id, $submission_time, $weblink, $warning_message);

sub prepareWorkDirectory {
        -d $WORK_DIRECTORY or confess "Error: work directory $WORK_DIRECTORY does not exist";
        -f "$WORK_DIRECTORY/submission_id" or confess "Error: submission_id file does not exist in work directory $WORK_DIRECTORY";

        open (SUBMISSION_ID, "$SUBMISSION_ID_FILENAME") or confess "Error: cannot open submission_id file in work directory $WORK_DIRECTORY: $!";
        flock SUBMISSION_ID, 1;
        $submission_id = <SUBMISSION_ID>;
        flock SUBMISSION_ID, 8;
        close (SUBMISSION_ID);
        $submission_id++;

	#Xiao added the following line to generate the result link ahead of running annovar.
	my $maxLenth=16;
        my @a = (0..9,'a'..'z','A'..'Z','-','_');
        my $password = join '', map { $a[int rand @a] } 0..($maxLenth-1);        
        $weblink = qq (http://wannovar.usc.edu/done/$submission_id/$password/index.html) ;
               
	mkdir ("$WORK_DIRECTORY/$submission_id") or confess "Error: cannot generate submission directory for submission id $submission_id: $!";
	chmod 0777, "$WORK_DIRECTORY/$submission_id" or confess "Error: unable to set the permission of directories: $!";
	
	if ($variant_call or $paste_variant) {
		if ($variant_call) {
			my $orig_file = "$WORK_DIRECTORY/$submission_id/query.orig.vcf";
			if ($variant_call=~/.*\.gz$/) {
				$orig_file = "$WORK_DIRECTORY/$submission_id/query.orig.vcf.gz";
			}
			elsif ($variant_call=~/.*\.zip$/) {
				$orig_file = "$WORK_DIRECTORY/$submission_id/query.orig.vcf.zip";
			}
		open (VCF, ">$orig_file") or confess "Error: cannot write query.orig.vcf file: $!";
	        binmode VCF;
	        while (<$variant_call_fh>) {
	                print VCF;
	        }
	        close (VCF);
	    if ($variant_call=~/.*\.gz$/) {
			system ("gunzip $orig_file") and warn "Error gunzip $orig_file";
			}
			elsif ($variant_call=~/.*\.zip$/) {
			  system ("mkdir $WORK_DIRECTORY/$submission_id/zipdir")	and warn "Error make zip directory";
			  system ("unzip $orig_file -d $WORK_DIRECTORY/$submission_id/zipdir >$WORK_DIRECTORY/$submission_id/ttt") and warn "Error unzip $orig_file";
			  system ("mv $WORK_DIRECTORY/$submission_id/zipdir/* $WORK_DIRECTORY/$submission_id/query.orig.vcf") and warn "Error unzip $orig_file";	
			}
	        
	} elsif ($paste_variant){
	  	    open (VCF, ">$WORK_DIRECTORY/$submission_id/query.orig.vcf") or confess "Error: cannot write query.orig.vcf file: $!";
	  	    print VCF $paste_variant;
	  	    close (VCF);
	  	  }    
		if (-z "$WORK_DIRECTORY/$submission_id/query.orig.vcf") {  
			system ("rm -rf $WORK_DIRECTORY/$submission_id") and confess "Error rm -rf";
			display_error ("Unable to read the uploaded ANNOVAR input file: please make sure that the file exists and it is in standard ANNOVAR input format!", $CARETAKER);
        	}
		
		my $sum_output = '';
		-f "$BIN_DIRECTORY/convert2annovar.pl" or confess "Error: cannot execute the convert2annovar.pl program: program does not exist";
		-x "$BIN_DIRECTORY/convert2annovar.pl" or confess "Error: cannot execute the convert2annovar.pl program: access denied";
		
		if ($vcf_dp){
		$vcf_dp = " -coverage $vcf_dp";
	  }
	  if ($vcf_qd){
		$vcf_qd = " -snpqual $vcf_qd";
	  }
    		
		open (ANNOVAR, "-|", "$BIN_DIRECTORY/convert2annovar.pl $WORK_DIRECTORY/$submission_id/query.orig.vcf -format $input_fmt -includeinfo -withzyg".$vcf_dp.$vcf_qd." -out $WORK_DIRECTORY/$submission_id/query.annovar.avinput 2>&1") or confess "$BIN_DIRECTORY/convert2annovar.pl $WORK_DIRECTORY/$submission_id/query.orig.vcf -format $input_fmt -out $WORK_DIRECTORY/$submission_id/query.annovar.avinput 2>&1";
		   
		while (<ANNOVAR>) {
			$sum_output .= $_;          
		}
		close(ANNOVAR);
                if (-z "$WORK_DIRECTORY/$submission_id/query.annovar.avinput") {
                        system ("rm -rf $WORK_DIRECTORY/$submission_id") and confess "Error rm -rf";
                        display_error ("Unable to read the uploaded ANNOVAR input file: please make sure that the file exists and it is in standard ANNOVAR input format!", $CARETAKER);
                }
		if ($sum_output =~ m/(Error.+\n?)/) { 
			system ("rm -rf $WORK_DIRECTORY/$submission_id") and confess "Error rm -rf";
			display_error ($1, $CARETAKER);          
		}
		else {
			$sum_output =~ m/NOTICE: Read (\d+) lines and wrote (.+\n?)/;
			$warning_message = "A summary of variants(input file): <b>User input contains $1 lines; wANNOVAR found $2.</b>";
			chomp $warning_message ;
			if($sum_output =~ m/(WARNING.+\n?)/){
				$warning_message .= "<br>$1";
			}
		}

	}
      
	#control file    
	my $control_flag="F";
  if ($control_call or $paste_control) {
  if ($control_call) {
  	  my $orig_file = "$WORK_DIRECTORY/$submission_id/control.orig.vcf";
  	  if ($control_call=~/.*\.gz$/) {
			$orig_file = "$WORK_DIRECTORY/$submission_id/control.orig.vcf.gz";
			}
			elsif ($control_call=~/.*\.zip$/) {
		  $orig_file = "$WORK_DIRECTORY/$submission_id/control.orig.vcf.zip";
			} 
	        open (VCF, ">$orig_file") or confess "Error: cannot write control.orig.vcf file: $!";
	        while (<$control_call_fh>) {
	                print VCF;
	        }
	        close (VCF);
	    if ($control_call=~/.*\.gz$/) {
			system ("gunzip $orig_file") and warn "Error gunzip $orig_file";
			}
			elsif ($control_call=~/.*\.zip$/) {
		  system ("mkdir $WORK_DIRECTORY/$submission_id/zipdir1") and warn "Error make zip1 directory";
		  system ("unzip $orig_file -d $WORK_DIRECTORY/$submission_id/zipdir1") and warn "Error unzip $orig_file";
		  system ("mv $WORK_DIRECTORY/$submission_id/zipdir1/* $WORK_DIRECTORY/$submission_id/control.orig.vcf >$WORK_DIRECTORY/$submission_id/ttt") and warn "Error unzip $orig_file";

                  #system ("unzip $orig_file") and warn "Error unzip $orig_file";
			} 
	} elsif ($paste_control){
	  	    open (VCF, ">$WORK_DIRECTORY/$submission_id/control.orig.vcf") or confess "Error: cannot write control.orig.vcf file: $!";
	  	    print VCF $paste_control;
	  	    close (VCF);
	  	  }   
	if (-z "$WORK_DIRECTORY/$submission_id/control.orig.vcf") {  
			system ("rm -rf $WORK_DIRECTORY/$submission_id") and confess "Error rm -rf";
			display_error ("Unable to read the uploaded ANNOVAR control file: please make sure that the file exists and it is in standard ANNOVAR input format!", $CARETAKER);
        	}

		my $con_output = '';
		-f "$BIN_DIRECTORY/convert2annovar.pl" or confess "Error: cannot execute the convert2annovar.pl program: program does not exist";
		-x "$BIN_DIRECTORY/convert2annovar.pl" or confess "Error: cannot execute the convert2annovar.pl program: access denied";
		
#		if ($vcf_dp){
#		$vcf_dp = " -coverage $vcf_dp";
#	  }
#	  if ($vcf_qd){
#		$vcf_qd = " -snpqual $vcf_qd";
#	  }
	  	
		open (ANNOVAR, "-|", "$BIN_DIRECTORY/convert2annovar.pl $WORK_DIRECTORY/$submission_id/control.orig.vcf -format $input_fmt -includeinfo -withzyg".$vcf_dp.$vcf_qd." -out $WORK_DIRECTORY/$submission_id/control.annovar.avinput 2>&1") or confess "$BIN_DIRECTORY/convert2annovar.pl $WORK_DIRECTORY/$submission_id/control.orig.vcf -format $input_fmt -out $WORK_DIRECTORY/$submission_id/control.annovar.avinput 2>&1";
		while (<ANNOVAR>) {
			$con_output .= $_;          
		}
		close(ANNOVAR);
		if (-z "$WORK_DIRECTORY/$submission_id/control.annovar.avinput") {
                        system ("rm -rf $WORK_DIRECTORY/$submission_id") and confess "Error rm -rf";
                        display_error ("Unable to read the uploaded ANNOVAR input file: please make sure that the file exists and it is in standard ANNOVAR input format!", $CARETAKER);
                }
		if ($con_output =~ m/(Error.+\n?)/) { 
			system ("rm -rf $WORK_DIRECTORY/$submission_id") and confess "Error rm -rf";
			display_error ($1, $CARETAKER);          
		}
		else {
			$con_output =~ m/NOTICE: Read (\d+) lines and wrote (.+\n?)/;
			$warning_message .= "<br>A summary of variants(control file): <b>User control input contains $1 lines; wANNOVAR found $2.</b>";
			chomp $warning_message ;
			if($con_output =~ m/(WARNING.+\n?)/){
				$warning_message .= "<br>$1";
			}
		}  	  
 	$control_flag="T";
  }  
  	  	
  	    open (INFO, ">$WORK_DIRECTORY/$submission_id/info") or confess "Error: cannot write info file: $!";
        print INFO "sample_id=$sample_id\nreply_email=$reply_email\nsubmission_time=$submission_time\nreference_genome=$ref_genome\ngene_location=$input_gene\npassword=$password\n";
        $variant_call and print INFO "variant_file=$variant_call\n" and print INFO "variant_call=query.annovar.avinput\n"; ###should be a convert annovar input file (query.orig.vcf -> query.annovar.avinput)
        $paste_variant and print INFO "variant_file=custom input\n" and print INFO "variant_call=query.annovar.avinput\n";
        
	##
	if ($vcf_qd or $vcf_dp) {
		my $fcon = `grep -v '^#' $WORK_DIRECTORY/$submission_id/query.orig.vcf | wc -l` - `cat $WORK_DIRECTORY/$submission_id/query.annovar.avinput | wc -l`; 
		print INFO "filtered_vcf=$fcon\n";
	}	
	##disease model added here
        if ($input_model eq "no") {
        	print INFO "filtering_model=no filtering\n";
        }
        elsif ($input_model eq "rr") {
        	print INFO "filtering_model=rare recessive disease\n";
        }
        elsif ($input_model eq "rd") {
        	print INFO "filtering_model=rare dominant disease\n";
        }
        elsif ($input_model eq "cr") {
        	print INFO "filtering_model=common recessive disease\n";
        }
        elsif ($input_model eq "custom") {
        	print INFO "filtering_model=custom\n";
        }
        
        print INFO "variant_format=$input_fmt\n";      
        print INFO "dbsnp_version=$dbsnp_ver\n";
        print INFO "MAF=$maf_value\n";
        print INFO "control=$control_flag\n";
#####
#####
##### 
        if(@step) {
        print INFO "step_f=$step_fs\n";
        print INFO "step_p=$step_fp\n";
	print INFO "step_des=$step_org\n"
        }
        
        print INFO "ip=$ip\n";
	print INFO "host=$host\n";

	close (INFO);
        if (-e "/var/www/html/annovar-server/html/done/$submission_id") {
        	system ("rm -rf /var/www/html/annovar-server/html/done/$submission_id") and confess "can not remove submission $submission_id folder";
        }
        mkdir ("/var/www/html/annovar-server/html/done/$submission_id") or confess "can not create submission $submission_id folder"; 
        mkdir ("/var/www/html/annovar-server/html/done/$submission_id/$password") or confess "can not remove submission $submission_id password $password folder";
        
        open (WAIT, ">/var/www/html/annovar-server/html/done/$submission_id/$password/index.html") or die "can not create file index.html";
        print WAIT "<html><META HTTP-EQUIV=refresh CONTENT=60><p>Your submission is being processed and will be available at this page after computation is done. This page will refresh every 60 seconds. </p><p>You can click <a href=\"http://wannovar.usc.edu/done/$submission_id/$password/index.html\">here</a> to refresh the page manually.</p></html>";
        close (WAIT);
        system("chmod 777 /var/www/html/annovar-server/html/done/$submission_id");
        system("chmod 777 /var/www/html/annovar-server/html/done/$submission_id/$password");
        system("chmod 777 /var/www/html/annovar-server/html/done/$submission_id/$password/index.html");
 
        open (SUBMISSION_ID, ">$SUBMISSION_ID_FILENAME") or confess "Error: cannot write submission_id file in work directory $WORK_DIRECTORY: $!";
        flock SUBMISSION_ID, 2;
        print SUBMISSION_ID $submission_id;
        flock SUBMISSION_ID, 8;
        close (SUBMISSION_ID);
        
#        if ($sample_id ne 'norun') {
#		defined(my $pid=fork()) or die "Fork process failured:$!\n";
#		if ($pid) {
#			1;
#		} else {
#			exec("/var/www/html/annovar-server/exec/control_annovar_dev.pl $submission_id") or confess "can not execute submission";       
#		}
#	}
}


sub generateFeedback {
	my ($submission_id, $submission_time, $weblink, $warning_message) = @_;
	my $page;
	open (TEMPLATE, "$SERVER_DIRECTORY/template.html") or confess "Error: cannot read from template file\n";
	while (<TEMPLATE>) {
		$page .= $_;
	}
	close (TEMPLATE);
	
	my $submission_summary = <<SUMMARY;
<h1> Submission received </h1>
<hr>
<p>Your submission ID <b>$submission_id</b> has been received by the ANNOVAR server at <b>$submission_time</b>. </p><p>The results will be generated at <a href="$weblink"><b>$weblink</b></a> after the computation is done.</p>
<P>$warning_message</p>
SUMMARY

	$page =~ s#<div id=cgi_response></div>#$submission_summary#;
	print $page;
}

sub display_error
{
	my ($error_message, $email_address) = @_;
	my $page;

	open (TEMPLATE, "$SERVER_DIRECTORY/template.html") or confess "Error: cannot read from template file\n";
	while (<TEMPLATE>) {
		$page .= $_;
	}
	close (TEMPLATE);
	
	my $submission_summary = <<SUMMARY;
<h3> ERROR: $error_message </h3><hr><p> If this is not the expected result, please notify <var><a href=\"mailto:$email_address\">$email_address</a></var> of this error. Thank you.</p>
SUMMARY
        $page =~ s#<div id=cgi_response></div>#$submission_summary#;
	print $page;
	exit(0);
}

sub check_avinput{
	open (FL, "$WORK_DIRECTORY/$submission_id/query.orig.vcf") or die"Error: cannot open query.orig.vcf file";
	while(<FL>) {
		my @tp = split /\t/, $_;
		if ($tp[2] =~ /\d+/) {
			return (1);
		}
		else {
			return(0);
			last;
		}
	}
	close(FL);
}



sub check_ip{
my $dir="/var/www/html/annovar-server/exec/work";
my $cnt=0;
#my $dir="/var/www/html/annovar-server/html/done";

#chdir($dir);
my (@id, %info);
opendir(DH, "$dir") or die "Can't open: $!\n" ;

foreach (sort readdir(DH)) {
if ($_ eq '.' || $_ eq '..') {
next;
}
my $fd = $_;
if (-d "$dir/$_"){
push @id, $_;
open (INFO, "$dir/$_/info") or warn "Error: cannot read info file $dir/$_/info: $!";
while (<INFO>) {
        chomp;
        my ($key, $value) = split ('=', $_);
        $info{$key} = $value;
}
close (INFO);
if (($ip eq $info{"ip"}) and ($host eq $info{"host"})){
$cnt++;
}
if ($cnt>=10) {
display_error("sorry, you cannot process more than 4 jobs at a time from the same IP address; wait after your previous submission is finished.", $CARETAKER);
}
}
}

closedir(DH);
}
