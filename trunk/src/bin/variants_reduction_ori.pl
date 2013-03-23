#!/usr/bin/perl
use warnings;
use strict;
use Pod::Usage;
use Getopt::Long;

our $VERSION = 			'$Revision: 512 $';
our $LAST_CHANGED_DATE =	'$LastChangedDate: 2012-11-01 14:38:01 -0700 (Thu, 01 Nov 2012) $';

our ($verbose, $help, $man);
our ($queryfile, $dbloc);
our ($outfile, $buildver, $remove, $checkfile, $dispensable, $genetype, $maf_threshold, $protocol, $operation, $genericdbfile,
	$ljb_sift_threshold, $ljb_pp2_threshold);
our ($file1000g);

GetOptions('verbose|v'=>\$verbose, 'help|h'=>\$help, 'man|m'=>\$man, 'outfile=s'=>\$outfile, 'buildver=s'=>\$buildver, 'remove'=>\$remove,
	'checkfile!'=>\$checkfile, 'dispensable=s'=>\$dispensable, 'genetype=s'=>\$genetype,
	'maf_threshold=f'=>\$maf_threshold, 'protocol=s'=>\$protocol, 'operation=s'=>\$operation, 'genericdbfile=s'=>\$genericdbfile, 
	'ljb_sift_threshold=f'=>\$ljb_sift_threshold, 'ljb_pp2_threshold=f'=>\$ljb_pp2_threshold) or pod2usage ();
	
$help and pod2usage (-verbose=>1, -exitval=>1, -output=>\*STDOUT);
$man and pod2usage (-verbose=>2, -exitval=>1, -output=>\*STDOUT);
@ARGV or pod2usage (-verbose=>0, -exitval=>1, -output=>\*STDOUT);
@ARGV == 2 or pod2usage ("Syntax error");

my $path = $0;
$path =~ s/[^\\\/]+$//;
$path and $ENV{PATH} = "$path:$ENV{PATH}";		#set up the system executable path to include the path where this program is located in

($queryfile, $dbloc) = @ARGV;

$outfile ||= $queryfile;
$genetype ||= 'refgene';
$genetype =~ m/^refgene|knowngene|ensgene|gencodegene$/i or $genetype =~ m/wgEncodeGencode\w+$/ or pod2usage ("Error in argument: the --genetype can be 'refgene', 'knowngene' or 'ensgene' only");

if ($genetype eq 'gencodegene') {
	if ($buildver eq 'hg18') {
		$genetype = 'wgEncodeGencodeManualV3';
	} elsif ($buildver eq 'hg19') {
		$genetype = 'wgEncodeGencodeManualV4';
	}
}

if (not defined $buildver) {
	$buildver = 'hg18';
	print STDERR "NOTICE: the --buildver argument is set as 'hg18' by default\n";
}
$buildver eq 'hg18' or $buildver eq 'hg19' or pod2usage ("Error in argument: the --buildver argument must be 'hg18' or 'hg19'");


if (defined $maf_threshold) {
	$maf_threshold >= 0 and $maf_threshold <= 1 or pod2usage ("Error: the --maf_threshold argument must be between 0 and 1 inclusive");
}

not defined $checkfile and $checkfile = 1;

if (not $protocol) {
	$operation and pod2usage ("Error in argument: you must specify --protocol if you specify --operation");
	if ($buildver eq 'hg18') {
		$protocol = 'nonsyn_splicing,1000g2010jul_ceu,1000g2010jul_jptchb,1000g2010jul_yri,snp132,esp5400_ea,esp5400_aa,recessive';
		$operation = 'g,f,f,f,f,f,f,m';
		print STDERR "NOTICE: the --protocol argument is set as 'nonsyn_splicing,1000g2010jul_ceu,1000g2010jul_jptchb,1000g2010jul_yri,snp132,esp5400_ea,esp5400_aa,recessive' by default\n";
	} elsif ($buildver eq 'hg19') {
		$protocol = 'nonsyn_splicing,1000g2012feb_all,snp135,esp5400_ea,esp5400_aa,recessive';
		$operation = 'g,f,f,f,f,m';
		print STDERR "NOTICE: the --protocol argument is set as 'nonsyn_splicing,1000g2012feb_all,snp135,esp5400_ea,esp5400_aa,recessive' by default\n";
	}
}

if ($protocol =~ m/\bgeneric\b/) {
	$genericdbfile or pod2usage ("Error in argument: please specify -genericdbfile argument when 'generic' operation is specified");
}

my @protocol = split (/,/, $protocol);
my @operation = split (/,/, $operation);
my $sc;
my $linecount;

my (%valistep, $skip);

@protocol == @operation or pod2usage ("Error in argument: different number of elements are specified in --protocol and --operation argument");

for my $op (@operation) {
	$op =~ m/^g|r|f|m$/ or pod2usage ("Error in argument: the --operation argument must be comma-separated list of 'g', 'r', 'f' or 'm'");
}

$checkfile and checkFileExistence ();

system ("cp $queryfile $outfile.step0.varlist");
for my $i (0 .. @protocol-1) {
	print STDERR "-----------------------------------------------------------------\n";
	print STDERR "NOTICE: Processing operation=$operation[$i] protocol=$protocol[$i]\n";
	if ($operation[$i] eq 'g') {
		geneOperation ($i+1, "$outfile.step$i.varlist", $protocol[$i]);
	} elsif ($operation[$i] eq 'r') {
		regionOperation ($i+1, "$outfile.step$i.varlist", $protocol[$i]);
	} elsif ($operation[$i] eq 'rr') {
		regionOperation ($i+1, "$outfile.step$i.varlist", $protocol[$i], 1);
	} elsif ($operation[$i] eq 'f') {
		filterOperation ($i+1, "$outfile.step$i.varlist", $protocol[$i]);
	} elsif ($operation[$i] eq 'm') {
		modelOperation ($i+1, "$outfile.step$i.varlist", $protocol[$i]);
	}
}




sub geneOperation {
	my ($step, $infile, $operation) = @_;
	
	if ($operation eq 'nonsyn_splicing' or $operation eq 'nonsyn') {
		$sc = "annotate_variation.pl -geneanno -buildver $buildver -dbtype $genetype -outfile $outfile.step$step $infile $dbloc";
		print STDERR "\nNOTICE: Running step $step with system command <$sc>\n";
		system ($sc) and die "Error running system command: <$sc>\n";
		system ("fgrep -v -w synonymous $outfile.step$step.exonic_variant_function | fgrep -v -w nonframeshift | cut -f 4- > $outfile.step$step.varlist");
		
		$operation eq 'nonsyn_splicing' and system ("fgrep -w splicing $outfile.step1.variant_function | fgrep -w -v exonic | cut -f 3- >> $outfile.step$step.varlist");
		
		system ("sort $outfile.step$step.varlist | uniq > $outfile.step$step.varlist.temp; mv $outfile.step$step.varlist.temp $outfile.step$step.varlist");
		
		$remove and unlink ("$outfile.step1.varlist");
		$linecount = qx/cat $outfile.step$step.varlist | wc -l/; chomp $linecount;
		$linecount or warn "WARNING: No variants were left in analysis after this step. Program exits.\n" and exit;
		print STDERR "NOTICE: After step $step, $linecount variants are left in analysis.\n";
	} else {
		die "Error: the $operation command for gene-based annotation is not supported\n";
	}
}

sub regionOperation {
	my ($step, $infile, $dbtype, $reverse) = @_;
	$sc = "annotate_variation.pl -regionanno -dbtype $dbtype -buildver $buildver -outfile $outfile.step$step $infile $dbloc";
	print STDERR "\nNOTICE: Running step $step with system command <$sc>\n";
	system ($sc) and die "Error running system command: <$sc>\n";
	if ($reverse) {
		system ("cut -f 3- $outfile.step$step.${buildver}_$dbtype > $outfile.step$step.temp");
		system ("fgrep -v -f $outfile.step$step.temp $infile >  $outfile.step$step.varlist");
	} else {
		system ("cut -f 3- $outfile.step$step.${buildver}_$dbtype > $outfile.step$step.varlist");
	}
	
	$remove and unlink ("$outfile.step$step.varlist", "$outfile.step$step.${buildver}_$dbtype");
	$linecount = qx/cat $outfile.step$step.varlist | wc -l/; chomp $linecount;
	$linecount or warn "WARNING: No variants were left in analysis after this step. Program exits.\n" and exit;
	print STDERR "NOTICE: After step $step, $linecount variants are left in analysis.\n";
}

sub filterOperation {
	my ($step, $infile, $dbtype) = @_;
	$sc = "annotate_variation.pl -filter -dbtype $dbtype -buildver $buildver -outfile $outfile.step$step $infile $dbloc";
	
	if ($dbtype eq 'generic') {
		$sc .= " -genericdbfile $genericdbfile";
	}
	
	if ($dbtype eq 'ljb_sift') {
		my $score_threshold = $ljb_sift_threshold || 0.95;
		$sc .= " -score_threshold $score_threshold -reverse";
	}
	
	if ($dbtype eq 'ljb_pp2') {
		my $score_threshold = $ljb_pp2_threshold || 0.85;
		$sc .= " -score_threshold $score_threshold -reverse";
	}
	
	if (defined $maf_threshold) {
		if ($dbtype =~ m/^1000g/) {
			$sc .= " -maf_threshold $maf_threshold";
		} elsif ($dbtype =~ m/^esp\d+/ or $dbtype =~ m/^cg\d+/) {
			$sc .= " -score_threshold $maf_threshold";
		}
	}
	print STDERR "\nNOTICE: Running step $step with system command <$sc>\n";
	system ($sc) and die "Error running system command: <$sc>\n";
	
	my $dbtype1 = $dbtype;
	if ($dbtype =~ m/^1000g_(\w+)/) {
		$dbtype1 = uc ($1) . ".sites.2009_04";
	} elsif ($dbtype =~ m/^1000g2010_(\w+)/) {
		$dbtype1 = uc ($1) . ".sites.2010_03";
	} elsif ($dbtype =~ m/^1000g(20\d\d)([a-z]{3})_([a-z]+)$/) {
		my %monthhash = ('jan'=>'01', 'feb'=>'02', 'mar'=>'03', 'apr'=>'04', 'may'=>'05', 'jun'=>'06', 'jul'=>'07', 'aug'=>'08', 'sep'=>'09', 'oct'=>'10', 'nov'=>'11', 'dec'=>'12');
		$dbtype1 = uc ($3) . ".sites.$1" . '_' . $monthhash{$2};
	}
		
	system ("cp $outfile.step$step.${buildver}_${dbtype1}_filtered $outfile.step$step.varlist");		#use dbtype1, not dbtype!!!

	$remove and unlink ("$outfile.step$step.varlist", "$outfile.step$step.${dbtype}_filtered", "$outfile.step$step.${dbtype}_dropped");
	$linecount = qx/cat $outfile.step$step.varlist | wc -l/; chomp $linecount;
	$linecount or warn "WARNING: No variants were left in analysis after this step. Program exits.\n" and exit;
	print STDERR "NOTICE: After step $step, $linecount variants are left in analysis.\n";
}

sub modelOperation {
	my ($step, $infile, $dbtype) = @_;
	$sc = "fgrep -f $infile $outfile.step1.exonic_variant_function | fgrep -v -w UNKNOWN | cut -f 2- > $outfile.step$step.varlist;";		#function, gene name, plus original input
	$sc .= "cut -f 3- $outfile.step$step.varlist > $outfile.step$step.temp;";			#list of all avinput
	$sc .= "fgrep -v -f $outfile.step$step.temp $infile > $outfile.step$step.temp1;";		#list of splicing variants
	$sc .= "fgrep -f $outfile.step$step.temp1 $outfile.step1.variant_function | fgrep splicing >> $outfile.step$step.varlist;";	#adding splicing variants to nonsyn variants
	print STDERR "\nNOTICE: Running step 8 with system command <$sc>\n";
	system ($sc);			#this command may generate error, because the $outfile.step8.temp1 file may be empty

	$remove and unlink ("$outfile.step$step.temp", "$outfile.step$step.temp1", "$outfile.step1.exonic_variant_function");


	my (%found, %varpos);		#count of gene, variant information of the variant
	open (VAR, "$outfile.step$step.varlist") or die "Error: cannot read from varlist file $outfile.step$step.varlist: $!\n";
	while (<VAR>) {
		my @field = split (/\t/, $_);
		$field[1] =~ s/,$//;
		$field[1] =~ s/\([^\(\)]+\)//g;		#handle situations such as splicing        EMG1(NM_006331:exon1:c.125+1T>GC,NM_006331:exon2:c.126-1T>GC)   
		
		$field[1] =~ m/^(\w+)/ or die "Error: invalid record in input file $outfile.step$step.varlist (gene name expected at second column): <$_>\n";
		my $gene = $1;
		$found{$gene}++;
		$varpos{$gene} .= "\t$field[1]";
		if (m/\bhom\b/) {
			$found{$gene}++;
		}
	}
	
	my $count_candidate_gene = 0;
	open (OUT, ">$outfile.step$step.genelist") or die "Error: cannot write to output file $outfile.step$step.genelist: $!\n";
	print OUT "Gene\tNumber_of_deleterious_alleles\tMutations\n";
	for my $key (keys %found) {
		if ($dbtype eq 'recessive') {
			if ($found{$key} >= 2) {
				print OUT "$key\t$found{$key}$varpos{$key}\n";
				$count_candidate_gene++;
			}
		} elsif ($dbtype eq 'dominant') {
			if ($found{$key} >= 1) {
				print OUT "$key\t$found{$key}$varpos{$key}\n";
				$count_candidate_gene++;
			}
		} else {
			die "Error: the model operation $dbtype specified in -operation argument is not supported\n";
		}
	}
	print STDERR "\nNOTICE: a list of $count_candidate_gene potentially important genes and the number of deleterious alleles in them are written to $outfile.step$step.genelist\n";
}

sub checkFileExistence {
	my @file;
	my %dbtype1 = ('gene'=>'refGene', 'refgene'=>'refGene', 'knowngene'=>'knownGene', 'ensgene'=>'ensGene', 'band'=>'cytoBand', 'cytoband'=>'cytoBand', 'tfbs'=>'tfbsConsSites', 'mirna'=>'wgRna',
			'mirnatarget'=>'targetScanS', 'segdup'=>'genomicSuperDups', 'omimgene'=>'omimGene', 'gwascatalog'=>'gwasCatalog', 
			'1000g_ceu'=>'CEU.sites.2009_04', '1000g_yri'=>'YRI.sites.2009_04', '1000g_jptchb'=>'JPTCHB.sites.2009_04', 
			'1000g2010_ceu'=>'CEU.sites.2010_03', '1000g2010_yri'=>'YRI.sites.2010_03', '1000g2010_jptchb'=>'JPTCHB.sites.2010_03',
			'1000g2010jul_ceu'=>'CEU.sites.2010_07', '1000g2010jul_yri'=>'YRI.sites.2010_07', '1000g2010jul_jptchb'=>'JPTCHB.sites.2010_07',
			'1000g2010nov_all'=>'ALL.sites.2010_11', '1000g2011may_all'=>'ALL.sites.2011_05'
			);
	for my $i (0 .. @protocol-1) {
		my $dbtype1;
		if ($operation[$i] eq 'g') {
			$dbtype1 = $dbtype1{$genetype} || $genetype;
		} elsif ($operation[$i] eq 'm') {
			next;
		} else {
			$dbtype1 = $dbtype1{$protocol[$i]} || $protocol[$i];
		}
		
		if ($protocol[$i] =~ m/^1000g(20\d\d)([a-z]{3})_([a-z]+)$/) {
			my %monthhash = ('jan'=>'01', 'feb'=>'02', 'mar'=>'03', 'apr'=>'04', 'may'=>'05', 'jun'=>'06', 'jul'=>'07', 'aug'=>'08', 'sep'=>'09', 'oct'=>'10', 'nov'=>'11', 'dec'=>'12');
			$dbtype1 = uc ($3) . '.sites.' . $1 . '_' . $monthhash{$2};
		}
		my $file = $buildver . "_" . $dbtype1 . ".txt";
		push @file, $file;
	}

	for my $i (0 .. @file-1) {
		my $dbfile = File::Spec->catfile ($dbloc, $file[$i]);
		-f $dbfile or die "Error: the required database file $dbfile does not exist. Please download it via -downdb argument by annotate_variation.pl.\n";
	}
}


=head1 SYNOPSIS

 variants_reduction.pl [arguments] <query-file> <database-location>

 Optional arguments:
        -h, --help                      print help message
        -m, --man                       print complete documentation
        -v, --verbose                   use verbose output
            --protocol <string>		comma-delimited strong specifying database protocol
            --operation <string>	comma-delimited string specifying type of operation
            --outfile <string>		output file name prefix
            --buildver <string>		genome build version (default: hg18)
            --remove			remove all temporary files
            --genetype <string>		gene definition (default: refgene)
            --maf_threshold <float>	MAF threshold in allele frequency data
            --(no)checkfile		check if database file exists (default: ON)
            --genericdbfile <file>	specify generic db file
            --ljb_sift_threshold <float>	specify the threshold for ljb_sift (default: 0.95)
            --ljb_pp2_threshold <float>	specify the threshold for ljb_pp2 (default: 0.85)
            

 Function: automatically run a pipeline on a list of variants (potentially 
 whole-genome SNPs from a patient with Mendelian disease) and identify a small 
 subset that are most likely causal for Mendelian diseases
 
 Example: #recessive disease
          variants_reduction.pl infile humandb/ -protocol nonsyn_splicing,1000g2010jul_ceu,1000g2010jul_jptchb,1000g2010jul_yri,esp5400_ea,esp5400aa,snp132NonFlagged,recessive -operation g,f,f,f,f,f,f,m
          variants_reduction.pl infile humandb/ -buildver hg19 -protocol nonsyn_splicing,1000g2012feb_all,esp5400_ea,esp5400_aa,snp135NonFlagged,recessive -operation g,f,f,f,f,m
                  
 Version: $LastChangedDate: 2012-11-01 14:38:01 -0700 (Thu, 01 Nov 2012) $

=head1 OPTIONS

=over 8

=item B<--help>

print a brief usage message and detailed explanation of options.

=item B<--man>

print the complete manual of the program.

=item B<--verbose>

use verbose output.

=item B<--outfile>

the prefix of output file names

=item B<--buildver>

specify the genome build version

=item B<--remove>

remove all temporary files. By default, all temporary files will be kept for 
user inspection, but this will easily clutter the directory.

=item B<--genetype>

specify the gene definition, such as refgene (default), ucsc known gene, ensembl 
gene and gencode gene.

=item B<--maf_threshold>

specify the MAF threshold for allele frequency databases. This argument works 
for 1000 Genomes Project, ESP database and CG (complete genomics) database.

=item B<--checkfile>

the program will check if all required database files exist before execution of annotation

=item B<--genericdbfile>

specify the genericdb file used in -dbtype generic

=item B<--ljb_sift_threshold>

specify the LJB_SIFT threshold for filter operation (default: 0.95)

=item B<--ljb_pp2_threshold>

specify the LJB_PP2 threshold for filter operation (default: 0.85)

=back

=head1 DESCRIPTION

ANNOVAR is a software tool that can be used to functionally annotate a list of 
genetic variants, possibly generated from next-generation sequencing 
experiments. For example, given a whole-genome resequencing data set for a human 
with specific diseases, typically around 3 million SNPs and around half million 
insertions/deletions will be identified. Given this massive amounts of data (and 
candidate disease- causing variants), it is necessary to have a fast algorithm 
that scans the data and identify a prioritized subset of variants that are most 
likely functional for follow-up Sanger sequencing studies and functional assays.

by default, for hg18, the arguments are

variants_reduction.pl x1.avinput humandb -protocol nonsyn_splicing,1000g2010jul_ceu,1000g2010jul_jptchb,1000g2010jul_yri,snp132,esp5400_ea,esp5400_aa,recessive -operation g,f,f,f,f,f,f,m

for hg19, the arguments are

variants_reduction.pl x1.avinput humandb -protocol nonsyn_splicing,1000g2012feb_all,snp135,esp5400_ea,esp5400_aa,recessive -operation g,f,f,f,m


ANNOVAR is freely available to the community for non-commercial use. For 
questions or comments, please contact kai@openbioinformatics.org.


=cut