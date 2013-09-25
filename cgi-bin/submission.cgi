#!/usr/bin/env perl

use strict;
use warnings;
use CGI::Pretty;
use CGI::Carp qw/fatalsToBrowser/;
use FindBin qw/$RealBin/;
use lib "$RealBin/../lib";
use Utils;
#use Captcha::reCAPTCHA;
use File::Spec;


#read global configurations
my %server_conf=&Utils::readServConf("$RealBin/../conf/enlight_server.conf","$RealBin/..")
    or die "Reading server configuration file failed!\n";

#read list of available locuszoom databases
my $flank_default=$server_conf{"flank_default"} || "200";
my $generic_table_max=$server_conf{"generic_table_max"} || 10;
#my $public_key=$server_conf{'public_key'} or die "No public key for reCAPTCHA\n";

my @ref=('hg18','hg19');
my $ref_default='hg19';
my %ref_label=('hg19'=>'hg19','hg18'=>'hg18');

my @source_ref_pop= sort (map {$server_conf{$_}} grep { /^\d+$/ } (keys %server_conf) ); #/^\d/ since only keys are numeric, first one will be default
my %source_ref_pop_label=map {($_,$_)} @source_ref_pop; 
my ($default_source_ref_pop)=grep {/$ref_default/ and /EUR/i} @source_ref_pop;

my @non_generic_table=('recomb_rate','refFlat','refsnp_trans', 'snp_pos');
my $db=$server_conf{$ref_default."db"}; #only use table list from one db, don't forget to check the other one!
my @generic_table= sort &listGeneric (  $db,@non_generic_table );
push @generic_table,"" unless @generic_table; #no generic plot if using empty database

my %generic_table_label=map {($_,$_)} @generic_table;
my @qformat=("whitespace","space","comma");
my %qformat_label=map {($_,$_)} @qformat;
my $qformat_default="whitespace";
my @chr=(1..22,'X');
my %chr_label=map {($_,$_)} @chr;

################html generation###############
my $q=new CGI::Pretty;
#my $c=new Captcha::reCAPTCHA;

#print $q->header; #not useful unless read by APACHE directly
my $disable_table_css=".table_disable{visibility:hidden}";
print $q->start_html(
    -title=>"Enlight Homepage",
    -script=>{
	-language=>'javascript',
	-src=>'/javascript/lib.js',
    },
    -style=>{
	#-src=>'/style/style.css',
	-code=>$disable_table_css,
    },
);
##change reCAPTCHA theme here
#print <<RECAPTCHA;
#<script type="text/javascript">
# var RecaptchaOptions = {
#    theme : 'clean'
# };
# </script>
#RECAPTCHA
print $q->start_form(-name=>'main',-action=>"/cgi-bin/process.cgi",-method=>"post");
print $q->table(
    {-border=>0},
    $q->Tr(
	$q->td("Email (optional)"),
	$q->td($q->textfield(-name=>'email')),
    ),
    $q->Tr(
	$q->td("Input file (first line must be header)"),
	$q->td($q->filefield(-name=>"query")),
	$q->td(
	    $q->p($q->a({-href=>"/example/rs10318.txt"},"example file (plot using default settings)"))
	),
    ),
    $q->Tr(
	$q->td("Field delimiter"),
	$q->td($q->radio_group(-name=>"qformat",-values=>\@qformat,-labels=>\%qformat_label,-default=>$qformat_default)),
    ),
    $q->Tr(
	$q->td("Marker Column (case sensitive)"),
	$q->td($q->textfield(-name=>'markercol',-default=>'dbSNP135')),
    ),
    $q->Tr(
	$q->td("P value column (case-sensitive)"),
	$q->td($q->textfield(-name=>"pvalcol",-default=>'p')),
    ),
    $q->Tr(
	$q->td('Genome Build/LD source/Population'),
	$q->td(
	    $q->popup_menu(-name=>'source_ref_pop',-values=> \@source_ref_pop,-labels=>\%source_ref_pop_label,-default=>[$default_source_ref_pop])
	),
    ),
);

print $q->p($q->b("Fill one of the columns"));
print $q->table(
    {-border=>1,-rules=>'cols'},

    $q->Tr(
	$q->td ( 
	    $q->popup_menu(
		-name=>'select_region',
		-onchange=>'response_to_select_region(this.form.select_region.value)',
		-values=> ["snp","gene","chr"],
		-labels=> {"snp"=>"Reference SNP","gene"=>"Reference Gene","chr"=>"Chromosomal Region"},) 
	    	-default=> ["snp"],
	),
    ),
    $q->Tr(
	$q->td( {-id=>'snp',-style=>'display:block'},
	    $q->table( 
		$q->Tr($q->td("Reference SNP")),
		$q->Tr($q->td($q->textfield(-name=>"refsnp",-default=>"rs10318"))),
		$q->Tr($q->td("SNP Flanking region (Kb)")),
		$q->Tr($q->td($q->textfield(-name=>"snpflank",-default=>$flank_default))),
	    )
	),
	$q->td( {-id=>'gene',-style=>'display:none'},
	    $q->table( 
		$q->Tr($q->td("Reference Gene")),
		$q->Tr($q->td($q->textfield(-name=>"refgene"))),
		$q->Tr($q->td("Gene Flanking region (Kb)")),
		$q->Tr($q->td($q->textfield(-name=>"geneflank",-default=>$flank_default))),
	    )
	),
	$q->td( {-id=>'chr',-style=>'display:none'},
	    $q->table(
		$q->Tr($q->td("Chromosomal region")),
		$q->Tr($q->td(
			$q->popup_menu(-name=>'chr',-values=> \@chr,-labels=>\%chr_label,-default=>'15')
		    )
		),
		$q->Tr(
		    $q->td(
			["Start (Mb)",$q->textfield(-name=>'start')] ) 
		),
		$q->Tr(
		    $q->td(
			["End (Mb)",$q->textfield(-name=>"end")] )
		),
	    )
	),
    ),
);

print $q->p($q->b("Generic plot (using UCSC BED tables)"));
print $q->table(
    $q->Tr(
	$q->td($q->checkbox(-name=>'generic_toggle',-checked=>1,-label=>'Generic plot?')), #return 'on' if checked
    ),
    $q->Tr(
	$q->td(
	    $q->checkbox(-name=>'anno_toggle',-checked=>0,-label=>'Output ANNOVAR annotation?'),
	),
    ),
    $q->Tr(
	$q->td(
	    $q->checkbox(-name=>'avinput',-checked=>0,-label=>'Input file in ANNOVAR format?'),
	),
    ),
    $q->Tr(
	$q->td("Missing value for OUTPUT"),
	$q->td($q->textfield(-name=>'nastring',-default=>'NA')),
    ),
);
print $q->table(
    {-border=>1,-rules=>'rows'},
    $q->Tr(
	$q->td("Genome Build"),
	$q->td($q->radio_group(-name=>'ref',-values=>\@ref,-default=>$ref_default,-labels=>\%ref_label)),
    ),
    $q->Tr(
	$q->td("Generic data track"),
	$q->td($q->checkbox_group(-name=>'generic_table',-values=>\@generic_table,-linebreak=>'true',-labels=>\%generic_table_label)),
    ),
);
#print $c->get_html($public_key);
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
