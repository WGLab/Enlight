#!/usr/bin/perl
#-T taint checking

use strict;
use warnings;
use CGI::Pretty;
use CGI::Carp qw/fatalsToBrowser/;
use FindBin qw/$RealBin/;
use lib "$RealBin/../lib";
use Utils;


#read global configurations
my %server_conf=Utils::readServConf("$RealBin/../conf/annoenlight_server.conf") or die "Reading server configuration file failed!\n";
$CGI::POST_MAX = 1024 * 1024 * $server_conf{'maxupload'}; #max upload size





#create a webpage
#read list of available locuszoom databases
my @ref_source_pop=sort {$a <=> $b } (grep {/^\d/} (keys %server_conf)); #/^\d/ since only keys are numeric
my %ref_source_pop_label=map {($_,$server_conf{$_})} @ref_source_pop; 
my $flank_default="200kb";

my $q=new CGI::Pretty;
print $q->header;
print $q->start_html(-title=>"AnnoEnlight Homepage");
print $q->start_form(-action=>"process.cgi",-method=>"post");
print $q->table(
    {-border=>0},
    $q->Tr(
	$q->td("Input file"),
	$q->td($q->filefield(-name=>"query")),
    ),
    $q->Tr(
	$q->td("Marker Column"),
	$q->td($q->textfield('markercol')),
    ),
    $q->Tr(
	$q->td('Genome Build/LD source/Population'),
	$q->td(
	    $q->popup_menu(-name=>'ref_source_pop',-values=> \@ref_source_pop,-labels=>\%ref_source_pop_label)
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
	$q->td($q->textfield("pvalcol")),
    ),
);
print $q->p($q->submit("submit"),$q->reset());
print $q->end_form(),$q->end_html();


###############
=head
21March2013
return output via webpage, no email

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
