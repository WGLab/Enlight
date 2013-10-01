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

#my @non_generic_table=('recomb_rate','refFlat','refsnp_trans', 'snp_pos');
#my $db=$server_conf{$ref_default."db"}; #only use table list from one db, don't forget to check the other one!
#my @generic_table= sort &listGeneric (  $db,@non_generic_table );
#push @generic_table,"" unless @generic_table; #no generic plot if using empty database
#my %generic_table_label=map {($_,$_)} @generic_table;

my %tracks=&Utils::readObj("$RealBin/../conf/datatracks.txt");
my %cell= map { ($tracks{$_}{cell},$tracks{$_}{table}) } keys %tracks;
my %experiment= map { ($tracks{$_}{experiment},$tracks{$_}{table}) } keys %tracks;

my @qformat=("whitespace","space","comma");
my %qformat_label=map {($_,$_)} @qformat;
my $qformat_default="whitespace";
my @chr=(1..22,'X');
my %chr_label=map {($_,$_)} @chr;


my $jscode="
function changeTracks()
\{
    var insertPos=document.getElementById('dataTrackHere');
    var all=[ ".join(",\n",&genJsHash(%tracks))." ];

    var cell=document.getElementsByClassName('cell');
    var experiment=document.getElementsByClassName('experiment');

    var selectedCell=[];
    var selectedExperiment=[];
    var tracks=[];

    //get selected cell
    for (var i=0;i<cell.length;i++)
    \{
	if (cell[i].checked)
	\{
	    selectedCell.push(cell[i].value);
	\}
    \}

    //get selected assay
    for (var i=0;i<experiment.length;i++)
    \{
	if (experiment[i].checked)
	\{
	    selectedExperiment.push(experiment[i].value);
	\}
    \}

    //get selected tracks
    for (var i=0;i<all.length;i++)
    \{
	if (selectedCell.indexOf(all[i].cell) != -1)
	\{
	    if (selectedExperiment.indexOf(all[i].experiment) != -1)
	    \{
		tracks.push(all[i].name);
	    \}
	\}
    \}
    
    //remove all child nodes
    while(insertPos.firstChild)
    \{
	insertPos.removeChild(insertPos.firstChild);
    \}

    //add selected tracks
    for (var i=0;i<tracks.length;i++)
    \{
    	var newrow=document.createElement('tr');
    	var col=document.createElement('td');
    	var label=document.createElement('label');
    	var checkbox=document.createElement('input');
    	label.innerHTML=tracks[i];
    	checkbox.type='checkbox';
    	checkbox.value=tracks[i];
    	checkbox.name='generic_table';
    	checkbox.checked=true;

    	label.appendChild(checkbox);
    	col.appendChild(label);
    	newrow.appendChild(col);
    	insertPos.appendChild(newrow);
	if (i>".($generic_table_max-1).")
	\{
		alert('At most $generic_table_max tracks can be selected.');
		break;
	\}
	
    \}

    //add custom tracks upload fields
    for (var i=0;i<$generic_table_max-tracks.length;i++)
    \{
    	var newrow=document.createElement('tr');
    	var col=document.createElement('td');
    	var label=document.createElement('label');
    	var upload=document.createElement('input');
    	label.innerHTML='Custom track';
    	upload.type='file';
    	upload.name='custom_table';

    	label.appendChild(upload);
    	col.appendChild(label);
    	newrow.appendChild(col);
    	insertPos.appendChild(newrow);
    \}
\}

function response_to_select_region(input_value) 
\{
    snp=document.getElementById('snp');
    gene=document.getElementById('gene');
    chr=document.getElementById('chr');
    if (input_value=='snp')
    \{
	snp.style.display='block';
	gene.style.display='none';
	chr.style.display='none';
    \} else if (input_value=='gene')
    \{
	gene.style.display='block';
	snp.style.display='none';
	chr.style.display='none';
    \} else if (input_value=='chr')
    \{
	chr.style.display='block';
	snp.style.display='none';
	gene.style.display='none';
    \}
\}
";

################html generation###############
my $q=new CGI::Pretty;
#my $c=new Captcha::reCAPTCHA;

#print $q->header; #not useful unless read by APACHE directly
my $disable_table_css=".table_disable{visibility:hidden}";
print $q->start_html(
    -title=>"Enlight Homepage",
    -script=>{
	-language=>'javascript',
	#-src=>'/javascript/lib.js',
	-code=>$jscode,
    },
    -style=>{
	#-src=>'/style/style.css',
	-code=>$disable_table_css,
    },
    -onLoad=>"changeTracks()",

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

print $q->p($q->b("Specify a region"));
print $q->table(
    {-border=>1},
    $q->Tr(
	$q->td ( 
	    $q->popup_menu(
		-name=>'select_region',
		-onchange=>'response_to_select_region(this.form.select_region.value)',
		-values=> ["snp","gene","chr"],
		-labels=> {"snp"=>"Reference SNP","gene"=>"Reference Gene","chr"=>"Chromosomal Region"},
	    	-default=> ["snp"],
	    )
	),
    ),
    $q->Tr(
	$q->td( {-id=>'snp',-style=>'display:block'},
	    $q->table( 
		#$q->Tr($q->td("Reference SNP")),
		$q->Tr($q->td($q->textfield(-name=>"refsnp",-default=>"rs10318"))),
		$q->Tr($q->td("SNP Flanking Region (Kb)")),
		$q->Tr($q->td($q->textfield(-name=>"snpflank",-default=>$flank_default))),
	    )
	),
	$q->td( {-id=>'gene',-style=>'display:none'},
	    $q->table( 
		#$q->Tr($q->td("Reference Gene")),
		$q->Tr($q->td($q->textfield(-name=>"refgene"))),
		$q->Tr($q->td("Gene Flanking Region (Kb)")),
		$q->Tr($q->td($q->textfield(-name=>"geneflank",-default=>$flank_default))),
	    )
	),
	$q->td( {-id=>'chr',-style=>'display:none'},
	    $q->table(
		#$q->Tr($q->td("Chromosomal region")),
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
    $q->Tr(
	$q->td("Genome Build"),
	$q->td($q->radio_group(-name=>'ref',-values=>\@ref,-default=>$ref_default,-labels=>\%ref_label)),
    ),
);
print $q->table(
    {-border=>1,-rules=>'rows'},
    $q->Tr(
	$q->td(
	    $q->table(
		$q->Tr($q->td($q->strong("Cell Line"))),
		$q->Tr([
		    map { $q->td( 
			    $q->checkbox( {-id=>$_,-class=>'cell',-label=>$_,-checked=>0,-value=>$_,-onchange=>'changeTracks()',} )
			) } sort keys %cell
		    ]),
	    )
	),
	$q->td(
	    $q->table(
		$q->Tr($q->td($q->strong("Experiment Type"))),
		$q->Tr([
		    map { $q->td( 
			    $q->checkbox( {-id=>$_,-class=>'experiment',-label=>$_,-checked=>0,-value=>$_,-onchange=>'changeTracks()',} )
			) } sort keys %experiment
		    ]),
	    )
	),
	$q->td(
	    $q->table(
		$q->Tr($q->td($q->strong("Data Tracks"))),
		$q->Tr(
		    $q->td(
			$q->table( {-id=>'dataTrackHere'},)
		    ),
		),
	    ),
	),
    ),
    $q->Tr(
	$q->td({-colspan=>3},
	   $q->p($q->submit("submit"),$q->reset())
	),
    ),
);




#print $c->get_html($public_key);
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
sub genJsHash
{
    my %hash=@_;
    my @return;
    for my $i(values %hash)
    {
	my %tmp=%{$i};
	my @one;
	push @one,"\{name:'$tmp{table}'";
	push @one,"cell:'$tmp{cell}'";
	push @one,"experiment:'$tmp{experiment}'\}";
	push @return,join(",",@one);
    }
    return @return;
}
