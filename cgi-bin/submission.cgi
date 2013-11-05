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
my $admin_email=$server_conf{'admin'};
#my $public_key=$server_conf{'public_key'} or die "No public key for reCAPTCHA\n";

my @ref=('hg18','hg19');
my $ref_default='hg19';
my %ref_label=('hg19'=>'hg19','hg18'=>'hg18');

my @source_ref_pop= sort (map {$server_conf{$_}} grep { /^\d+$/ } (keys %server_conf) ); #/^\d/ since only keys are numeric, first one will be default
my %source_ref_pop_label=map {($_,$_)} @source_ref_pop; 
my ($default_source_ref_pop)=grep {/$ref_default/ and /EUR/i} @source_ref_pop;

my %tracks=&Utils::readObj("$RealBin/../conf/datatracks.txt");
my %cell= map { ($tracks{$_}{cell},$tracks{$_}{table}) } keys %tracks;
my %experiment= map { ($tracks{$_}{experiment},$tracks{$_}{table}) } keys %tracks;

my @qformat=("whitespace","space","comma");
my %qformat_label=map {($_,$_)} @qformat;
my $qformat_default="whitespace";
my @chr=(1..22,'X');


my $jscode="
function changeTracks()
{
var insertPos=document.getElementById('dataTrackHere');
var all=[ ".join(",\n",&genJsHash(%tracks))." ];

var cell=document.getElementsByClassName('cell');
var experiment=document.getElementsByClassName('experiment');

var selectedCell=[];
var selectedExperiment=[];
var tracks=[];

//get selected cell
for (var i=0;i<cell.length;i++)
{
if (cell[i].checked)
{
selectedCell.push(cell[i].value);
}
}

//get selected assay
for (var i=0;i<experiment.length;i++)
{
if (experiment[i].checked)
{
selectedExperiment.push(experiment[i].value);
}
}

//get selected tracks
for (var i=0;i<all.length;i++)
{
if (selectedCell.indexOf(all[i].cell) != -1)
{
if (selectedExperiment.indexOf(all[i].experiment) != -1)
{
tracks.push(all[i].name);
}
}
}

//remove all child nodes
while(insertPos.firstChild)
{
insertPos.removeChild(insertPos.firstChild);
}

//add selected tracks
for (var i=0;i<tracks.length;i++)
{
if (i>".($generic_table_max-1).")
{
alert('At most $generic_table_max tracks can be selected.');
break;
}
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

}

//add custom tracks upload fields
for (var i=0;i<$generic_table_max-tracks.length;i++)
{
var newrow=document.createElement('tr');
var col=document.createElement('td');
var label=document.createElement('label');
var upload=document.createElement('input');
label.innerHTML='Custom track (BED format)';
upload.type='file';
upload.name='custom_table';

label.appendChild(upload);
col.appendChild(label);
newrow.appendChild(col);
insertPos.appendChild(newrow);
}
}

function response_to_select_region(input_value)
{
var insert=document.getElementById('insertRegionHere');

//remove all child nodes
while(insert.firstChild)
{
insert.removeChild(insert.firstChild);
}

if (input_value=='snp')
{
var row1=document.createElement('tr');
var col1=document.createElement('td');
var input1=document.createElement('input');
input1.type='text';
input1.name='refsnp';
input1.value='rs10318';
row1.appendChild(col1.appendChild(input1));

var row2=document.createElement('tr');
var col2=document.createElement('td');
var input2=document.createElement('p');
input2.innerHTML='SNP Flanking Region (Kb)';
row2.appendChild(col2.appendChild(input2));

var row3=document.createElement('tr');
var col3=document.createElement('td');
var input3=document.createElement('input');
input3.type='text';
input3.name='snpflank';
input3.value='$flank_default';
row3.appendChild(col3.appendChild(input3));

insert.appendChild(row1);
insert.appendChild(row2);
insert.appendChild(row3);
} else if (input_value=='gene')
{
var row1=document.createElement('tr');
var col1=document.createElement('td');
var input1=document.createElement('input');
input1.type='text';
input1.name='refgene';
row1.appendChild(col1.appendChild(input1));

var row2=document.createElement('tr');
var col2=document.createElement('td');
var input2=document.createElement('p');
input2.innerHTML='Gene Flanking Region (Kb)';
row2.appendChild(col2.appendChild(input2));

var row3=document.createElement('tr');
var col3=document.createElement('td');
var input3=document.createElement('input');
input3.type='text';
input3.name='geneflank';
input3.value='$flank_default';
row3.appendChild(col3.appendChild(input3));

insert.appendChild(row1);
insert.appendChild(row2);
insert.appendChild(row3);
} else if (input_value=='chr')
{
var row1=document.createElement('tr');
var col1=document.createElement('td');
var input1=document.createElement('select');
input1.name='chr';
var list=[".join(',',map { "'$_'" } @chr)."];

for (var i=0;i<list.length;i++)
{
var option=document.createElement('option');
option.value=list[i];
option.innerHTML=list[i];
input1.appendChild(option);
}
row1.appendChild(col1.appendChild(input1));

var row2=document.createElement('tr');
var col2_1=document.createElement('td');
var col2_2=document.createElement('td');
var input2=document.createElement('input');
col2_1.innerHTML='Start (Mb)';
input2.type='text';
input2.name='start';
row2.appendChild(col2_1);
row2.appendChild(col2_2.appendChild(input2));

var row3=document.createElement('tr');
var col3_1=document.createElement('td');
var col3_2=document.createElement('td');
var input3=document.createElement('input');
col3_1.innerHTML='End (Mb)';
input3.type='text';
input3.name='end';
row3.appendChild(col3_1);
row3.appendChild(col3_2.appendChild(input3));

insert.appendChild(row1);
insert.appendChild(row2);
insert.appendChild(row3);
}
}
";

################html generation###############
my $q=new CGI::Pretty;
#my $c=new Captcha::reCAPTCHA;

#print $q->header; #not useful unless read by APACHE directly
my $disable_table_css="
.table_disable
{
visibility:hidden;
}

.table_align
{
    vertical-align:top;
}
";
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
-onLoad=>"changeTracks();response_to_select_region(document.getElementById('select_region_id').value);",
);
##change reCAPTCHA theme here
#print <<RECAPTCHA;
#<script type="text/javascript">
# var RecaptchaOptions = {
#    theme : 'clean'
# };
# </script>
#RECAPTCHA
print $q->noscript($q->h1("Your browser does not support JavaScript! </br>Please enable JavaScript to use Enlight."));
print $q->h2("Enlight: integrating GWAS results with biological annotations");
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
    ),
    $q->Tr(
	$q->td(
	    $q->p($q->a({-href=>"/example/sample_out.png"},"Example output")),
	),
	$q->td(
	    $q->p($q->a({-href=>"/example/rs10318.txt"},"Example input (plot using default settings)")),
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
		-id=>'select_region_id',
		-name=>'select_region',
		-onchange=>'response_to_select_region(this.form.select_region.value)',
		-values=> ["snp","gene","chr"],
		-labels=> {"snp"=>"Reference SNP","gene"=>"Reference Gene","chr"=>"Chromosomal Region"},
		-default=> ["snp"],
	    )
	),
    ),
    $q->Tr(
	$q->td(
	    $q->table({-id=>'insertRegionHere'},$q->p(""))
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
	$q->td(
	    $q->p(
		"Missing value for OUTPUT",
		$q->textfield(-name=>'nastring',-default=>'NA'),
	    )
	),
    ),
    $q->Tr(
	$q->td(
	    $q->p(
		"Genome Build",
		$q->radio_group(-name=>'ref',-values=>\@ref,-default=>$ref_default,-labels=>\%ref_label)
	    )
	),
    ),
);
print $q->table(
    {-border=>1},
    $q->Tr(
	$q->td( {-class=>'table_align'},
	    $q->table(
		$q->Tr($q->td($q->strong("Cell Line"))),
		$q->Tr([
		    map { $q->td( 
			    $q->checkbox( {-id=>$_,-class=>'cell',-label=>$_,-checked=>0,-value=>$_,-onchange=>'changeTracks()',} )
			) } sort keys %cell
		    ]),
	    )
	),
	$q->td( {-class=>'table_align'},
	    $q->table(
		$q->Tr($q->td($q->strong("Experiment Type"))),
		$q->Tr([
		    map { $q->td( 
			    $q->checkbox( {-id=>$_,-class=>'experiment',-label=>$_,-checked=>0,-value=>$_,-onchange=>'changeTracks()',} )
			) } sort keys %experiment
		    ]),
	    )
	),
	$q->td( {-class=>'table_align'},
	    $q->table(
		$q->Tr($q->td($q->strong("Data Tracks (max: $generic_table_max)"))),
		$q->Tr(
		    $q->td(
#the $q->p is necessary, otherwise, only 1 table tag will be printed
			$q->table( {-id=>'dataTrackHere'},$q->p(""))
		    ),
		),
	    ),
	),
    ),
);

print $q->table(
    $q->Tr(
	$q->td(
	    $q->p($q->submit("submit"),$q->reset())
	),
    ),
);

#print $c->get_html($public_key);
print $q->end_form(),$q->end_html();
print $q->p("Wang Lab, Zilkha Genetic Institute, University of Southern California");
print $q->p("Please send questions or comments to <strong>$admin_email</strong>") if $admin_email;

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
