#!/usr/bin/perl -T

use strict;
use warnings;
use CGI;
use CGI::Carp qw/fatalsToBrowser/;
use FindBin qw/$RealBin/;
use lib "$RealBin/../lib";
use Utils;
use Captcha::reCAPTCHA;
use File::Spec;


#read global configurations
my %server_conf=&Utils::readServConf("$RealBin/../conf/enlight_server.conf","$RealBin/..")
    or die "Reading server configuration file failed!\n";

#read list of available locuszoom databases
my $flank_default=$server_conf{"flank_default"};
my $generic_table_max=$server_conf{"generic_table_max"};

my @ref=('hg18','hg19');
my $ref_default='hg19';
my %ref_label=('hg19'=>'hg19','hg18'=>'hg18');

my @source_ref_pop= sort (map {$server_conf{$_}} grep { /^\d+$/ } (keys %server_conf) ); #/^\d/ since only keys are numeric, first one will be default
my %source_ref_pop_label=map {($_,$_)} @source_ref_pop; 

my @non_generic_table=('recomb_rate','refFlat','refsnp_trans', 'snp_pos');
my $db=$server_conf{$ref_default."db"}; #only use table list from one db, don't forget to check the other one!
my @generic_table= sort &listGeneric (  File::Spec->catfile($RealBin,"..",$db),@non_generic_table      );
push @generic_table,"" unless @generic_table; #no generic plot if using empty database

my %generic_table_label=map {($_,$_)} @generic_table;
my @qformat=("whitespace","tab","comma");
my %qformat_label=map {($_,$_)} @qformat;
my $qformat_default="whitespace";

################html generation###############
my $q=new CGI;
my $c=new Captcha::reCAPTCHA;

print $q->header,$q->start_html(-title=>"Enlight Homepage");
#change reCAPTCHA theme here
print <<RECAPTCHA;
<script type="text/javascript">
 var RecaptchaOptions = {
    theme : 'clean'
 };
 </script>
RECAPTCHA
print $q->start_form(-action=>"process.cgi",-method=>"post");
print $q->table(
    {-border=>0},
    $q->Tr(
	$q->td("Email (optional)"),
	$q->td($q->textfield(-name=>'email')),
    ),
    $q->Tr(
	$q->td("Input file"),
	$q->td($q->filefield(-name=>"query")),
    ),
    $q->Tr(
	$q->td("Field delimiter"),
	$q->td($q->radio_group(-name=>"qformat",-values=>\@qformat,-labels=>\%qformat_label,-default=>$qformat_default)),
    ),
    $q->Tr(
	$q->td("Marker Column"),
	$q->td($q->textfield(-name=>'markercol',-default=>'snpname')),
    ),
    $q->Tr(
	$q->td('Genome Build/LD source/Population'),
	$q->td(
	    $q->popup_menu(-name=>'source_ref_pop',-values=> \@source_ref_pop,-labels=>\%source_ref_pop_label)
	),
    ),
    $q->Tr(
	$q->td("Flanking region"),
	$q->td(
	    $q->textfield(-name=>"flank",-default=>$flank_default)
	),
    ),
    $q->Tr(
	$q->td("Reference SNP"),
	$q->td(
	    $q->textfield("refsnp")
	),
    ),
    $q->Tr(
	$q->td("P value column"),
	$q->td($q->textfield(-name=>"pvalcol",-default=>'p')),
    ),
);

print $q->p($q->b("Generic plot (using UCSC BED tables)"));
print $q->table(
    $q->Tr(
	$q->td($q->checkbox(-name=>'generic_toggle',-checked=>1,-label=>'Generic plot?')), #return 'ON' if checked
    ),
    $q->Tr(
	$q->td($q->checkbox(-name=>'anno_toggle',-checked=>1,-label=>'Output annotation?')), #return 'ON' if checked
    ),
);
print $q->table(
    {-border=>1},
    $q->Tr(
	$q->td($q->checkbox(-name=>'generic_toggle',-checked=>1,-label=>'Generic plot?')), #return 'ON' if checked
    ),
    $q->Tr(
	$q->td($q->checkbox(-name=>'anno_toggle',-checked=>1,-label=>'Output annotation?')), #return 'ON' if checked
    ),
    $q->Tr(
	$q->td("Genome Build"),
	$q->td($q->radio_group(-name=>'ref',-values=>\@ref,-default=>$ref_default,-labels=>\%ref_label)),
    ),
    $q->Tr(
	$q->td("Generic data track (Press Ctrl to select multiple tracks)"),
	$q->td($q->scrolling_list(-name=>'generic_table',-values=>\@generic_table,-multiple=>'true',-labels=>\%generic_table_label,-size=>10)),
    ),
);
print $c->get_html("reCAPTCHA_public_key");
print $q->p($q->submit("submit"),$q->reset());
print $q->end_form(),$q->end_html();


#--------------SUBROUTINE-----------------
sub listGeneric
{
    #return tables of db, non_generic ones removed
    my $db=shift;
    my @non_generic=@_;
    &Utils::sys_which('sqlite3') or die "Cannot find SQLite3\n";
    &Utils::sys_which('xargs') or die "Cannot find xargs\n";
    my $table_list=`sqlite3 $db .tables 2>/dev/null | xargs`;
    chomp $table_list;
    map {$table_list =~ s/$_//gi} @non_generic;
    $table_list =~ s/^\s+|\s+$//; #del leading or trailing whitespaces
    return (split /\s+/,$table_list);
}

}

###############
=head
21March2013
return output via webpage, and optionally, email

=head
To use generic plot in locuszoom

~/projects/locuszoom-encode/bin/locuszoom --build hg19 --markercol dbSNP135 --source 1000G_Nov2010 --pop EUR --metal rs10318_summary_mecc_ccfr.txt --flank 150kb --refsnp rs10318 --pvalcol ccfr_p --generic wgEncodeHaibMethyl450Caco2SitesRep1,wgEncodeHaibMethyl450Hct116HaibSitesRep1,wgEncodeRegTfbsClusteredV2,wgEncodeUwDnaseCaco2HotspotsRep1 --no-date --prefix xxx --plotonly


To plot w/o generic tracks

~/projects/locuszoom-encode/bin/locuszoom --build hg19 --markercol dbSNP135 --source 1000G_Nov2010 --pop EUR --metal rs10318_summary_mecc_ccfr.txt --flank 500kb --refsnp rs10318 --pvalcol ccfr_p --no-date --prefix xxx --no-cleanup


#submission administration database
serverdb=/home/yunfeiguo/projects/annoenlight/log/server.db
#error log file
serverlog=/home/yunfeiguo/projects/annoenlight/log/error.log
#executable dir
exedir=/home/yunfeiguo/projects/annoenlight/bin
#temporary dir
tmp=/tmp
#output dir
outdir=/home/yunfeiguo/projects/annoenlight/done
#max submission per IP
maxcount=4
#max upload size (in MB)
maxupload=200

=cut
