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
my %server_conf=&Utils::readServConf(File::Spec->catfile($RealBin,"../conf/enlight_server.conf"))
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

my $page;


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

function getCheckedRadio(radio_group) 
{
    for (var i = 0; i < radio_group.length; i++) 
    {
	var button = radio_group[i];
	if (button.checked) 
	{
	    return button;
	}
    }
    return undefined;
}

function response_to_select_region(input_value)
{

    var insert=document.getElementById('insertRegionHere');
    var radio_group=document.getElementsByName('region_method');
    var input_value=getCheckedRadio(radio_group).value;

    //remove all child nodes
    while(insert.firstChild)
    {
	insert.removeChild(insert.firstChild);
    }

    if (input_value=='snp')
    {
	var row1=document.createElement('tr');
	var col1_1=document.createElement('td');
	var col1_2=document.createElement('td');
	var input1=document.createElement('input');
	col1_1.innerHTML='Index SNP';
	input1.type='text';
	input1.name='refsnp';
	input1.id='refsnp_id';
	input1.onclick=function (){ this.value=''};
	row1.appendChild(col1_1);
	row1.appendChild(col1_2.appendChild(input1));

	var row2=document.createElement('tr');
	var col2_1=document.createElement('td');
	var col2_2=document.createElement('td');
	var input2=document.createElement('input');
	col2_1.innerHTML='Flanking region (Kb)';
	input2.type='text';
	input2.name='snpflank';
	input2.value='$flank_default';
	input2.onclick=function (){ this.value=''};
	row2.appendChild(col2_1);
	row2.appendChild(col2_2.appendChild(input2));

	insert.appendChild(row1);
	insert.appendChild(row2);
    } else if (input_value=='gene')
    {
	var row1=document.createElement('tr');
	var col1_1=document.createElement('td');
	var col1_2=document.createElement('td');
	var input1=document.createElement('input');
	col1_1.innerHTML='Reference Gene';
	input1.type='text';
	input1.name='refgene';
	input1.onclick=function (){ this.value=''};
	row1.appendChild(col1_1);
	row1.appendChild(col1_2.appendChild(input1));

	var row2=document.createElement('tr');
	var col2_1=document.createElement('td');
	var col2_2=document.createElement('td');
	var input2=document.createElement('input');
	col2_1.innerHTML='Flanking region (kb)';
	input2.type='text';
	input2.name='geneflank';
	input2.value='$flank_default';
	input2.onclick=function (){ this.value=''};
	row2.appendChild(col2_1);
	row2.appendChild(col2_2.appendChild(input2));

	var row3=document.createElement('tr');
	var col3_1=document.createElement('td');
	var col3_2=document.createElement('td');
	var input3=document.createElement('input');
	col3_1.innerHTML=('Optional Index SNP (default is SNP with lowest P value)');
	input3.type='text';
	input3.name='refsnp';
	input3.onclick=function (){ this.value=''};
	row3.appendChild(col3_1);
	row3.appendChild(col3_2.appendChild(input3));

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
	input2.onclick=function (){ this.value=''};
	row2.appendChild(col2_1);
	row2.appendChild(col2_2.appendChild(input2));

	var row3=document.createElement('tr');
	var col3_1=document.createElement('td');
	var col3_2=document.createElement('td');
	var input3=document.createElement('input');
	col3_1.innerHTML='End (Mb)';
	input3.type='text';
	input3.name='end';
	input3.onclick=function (){ this.value=''};
	row3.appendChild(col3_1);
	row3.appendChild(col3_2.appendChild(input3));

	var row4=document.createElement('tr');
	var col4_1=document.createElement('td');
	var col4_2=document.createElement('td');
	var input4=document.createElement('input');
	col4_1.innerHTML=('Optional Index SNP (default is SNP with lowest P value)');
	input4.type='text';
	input4.name='refsnp';
	input4.onclick=function (){ this.value=''};
	row4.appendChild(col4_1);
	row4.appendChild(col4_2.appendChild(input4));

	insert.appendChild(row1);
	insert.appendChild(row2);
	insert.appendChild(row3);
	insert.appendChild(row4);
    }
}
function clear_datatrack_selection()
{
    var cell=document.getElementsByClassName( 'cell');
    for (var i=0;i<cell.length;i++)
    {
	cell[i].checked=false;
    }
    var experiment=document.getElementsByClassName( 'experiment');
    for (var i=0;i<experiment.length;i++)
    {
	experiment[i].checked=false;
    }
}
function loadExampleSetting()
{
    document.getElementById('qformat_whitespace').checked=true;
    document.getElementById('markercol_id').value='dbSNP135';
    document.getElementById('pvalcol_id').value='p';
    document.getElementById('source_ref_pop_id').value='1000G_Aug2009,hg18,CEU';	
    document.getElementById('region_method_snp').checked=true;
    response_to_select_region();

    document.getElementById('refsnp_id').value='rs10318';
    document.getElementById('generic_toggle_id').checked=true;
    document.getElementById('anno_toggle_id').checked=true;
    document.getElementById('avinput_id').checked=true;
    document.getElementById('ref_hg19').checked=true;

    //clear data track selection
    clear_datatrack_selection();
    document.getElementById('Caco-2').checked=true;	
    document.getElementById('HCT116').checked=true;	
    document.getElementById('ChIP-seq_CTCF').checked=true;
    document.getElementById('ChIP-seq_H3K27ac').checked=true;
    changeTracks();
}
";

################html generation###############
my $q=new CGI::Pretty;
#my $c=new Captcha::reCAPTCHA;

#print $q->header; #not useful unless read by APACHE directly
$page.= 
"<script type=\"text/javascript\"> //<![CDATA[
$jscode
//]]></script>\n";
##change reCAPTCHA theme here
#$page.= <<RECAPTCHA;
#<script type="text/javascript">
# var RecaptchaOptions = {
#    theme : 'clean'
# };
# </script>
#RECAPTCHA
$page.= $q->noscript($q->h1("Your browser does not support JavaScript! </br>Please enable JavaScript to use Enlight."));
$page.= $q->start_form(-name=>'main',-action=>"/cgi-bin/process.cgi",-method=>"post");
$page.= $q->h2("Input");
$page.= $q->table(
    {-border=>0},
    $q->Tr(
	$q->td("<a class='button' href=\"/example/rs10318.txt\"><strong>Download example input</strong></a><br />(right click and save as)"),
	$q->td("<button type='button' onclick='loadExampleSetting()'>Load settings for example input</button>"),
    ),
    $q->Tr(
	$q->td("Email (optional)"),
	$q->td($q->textfield(-name=>'email')),
    ),
    $q->Tr(
	$q->td("Input file (first line must be header)"),
	$q->td($q->filefield(-name=>"query")),
    ),
    $q->Tr(
	$q->td("Field delimiter"),
	$q->td($q->radio_group(-name=>"qformat",-id=>"qformat_whitespace",-values=>\@qformat,-labels=>\%qformat_label,-default=>$qformat_default)),
    ),
    $q->Tr(
	$q->td("Marker Column (case sensitive)"),
	$q->td($q->textfield(-name=>'markercol',-id=>'markercol_id',-default=>'dbSNP135')),
    ),
    $q->Tr(
	$q->td("P value column (case-sensitive)"),
	$q->td($q->textfield(-name=>"pvalcol",-id=>'pvalcol_id',-default=>'p')),
    ),
    $q->Tr(
	$q->td('Genome Build/LD source/Population'),
	$q->td(
	    $q->popup_menu(-name=>'source_ref_pop',-id=>'source_ref_pop_id',-values=> \@source_ref_pop,-labels=>\%source_ref_pop_label,-default=>[$default_source_ref_pop])
	),
    ),
);

$page.= $q->h2("Specify a region");
$page.= $q->table(
    {-border=>1},
    $q->Tr(
	$q->td ( 
	    "<input type='radio' name='region_method' id='region_method_snp' value='snp'  onclick='response_to_select_region()' checked >Reference SNP<br>
	      <input type='radio' name='region_method' onclick='response_to_select_region()' value='gene'>Reference Gene<br>
	        <input type='radio' name='region_method' onclick='response_to_select_region()' value='chr'>Chromosomal Region<br>
		"
	),
    ),
    $q->Tr(
	$q->td(
	    $q->table({-id=>'insertRegionHere'},$q->p(""))
	),
    ),
);

$page.= $q->p($q->b("Generic plot (using UCSC BED tables)"));
$page.= $q->table( {-class=>'noborder'},
    $q->Tr(
	$q->td($q->checkbox(-name=>'generic_toggle',-id=>'generic_toggle_id',-checked=>1,-label=>'Generic plot?')), #return 'on' if checked
    ),
    $q->Tr(
	$q->td(
	    $q->checkbox(-name=>'anno_toggle',-id=>'anno_toggle_id',-checked=>0,-label=>'Output ANNOVAR annotation?'),
	),
    ),
    $q->Tr(
	$q->td(
	    $q->checkbox(-name=>'avinput',-id=>'avinput_id',-checked=>0,-label=>'Input file in ANNOVAR format?'),
	),
    ),
    $q->Tr(
	$q->td(
	    $q->p(
		"Genome Build",
		'<label>
		<input type="radio" name="ref" value="hg18">hg18
		</label>
		<label>
		<input type="radio" name="ref" id="ref_hg19" value="hg19" checked="checked">hg19
		</label>'
	    )
	),
    ),
);
$page.= $q->table(
    $q->Tr(
	$q->th(["Cell Line","Experiment Type","Data Tracks (max: $generic_table_max)"]),
    ),
    $q->Tr(
	$q->td( {-class=>'table_align'},
	    $q->table( {-class=>'noborder left_aln'},
		$q->Tr([
		    map { $q->td( 
			    $q->checkbox( {-id=>$_,-class=>'cell',-label=>$_,-checked=>0,-value=>$_,-onchange=>'changeTracks()',} )
			) } sort keys %cell
		    ]),
	    )
	),
	$q->td( {-class=>'table_align'},
	    $q->table( {-class=>'noborder left_aln'},
		$q->Tr([
		    map { $q->td( 
			    $q->checkbox( {-id=>$_,-class=>'experiment',-label=>$_,-checked=>0,-value=>$_,-onchange=>'changeTracks()',} )
			) } sort keys %experiment
		    ]),
	    )
	),
	$q->td( {-class=>'table_align'},
	    $q->table( {-class=>'noborder left_aln' -id=>'dataTrackHere'}, $q->p("")),
	    ),
    ),
);

$page.= $q->table( -class=>'noborder',
    $q->Tr(
	$q->td(
	    $q->p($q->submit("submit"),$q->reset())
	),
    ),
);

#print $c->get_html($public_key);
$page.= $q->end_form();
$page.= $q->p("Please send questions or comments to <strong>$admin_email</strong>") if $admin_email;

&template2real($page);
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
sub template2real
{
    my $content=shift;
    my $real_dir=File::Spec->catdir($RealBin,"..","html");
    my $template_dir=File::Spec->catdir($RealBin,"..","template");
    my $index_in=File::Spec->catfile($template_dir,"index.html");
    my $index_out=File::Spec->catfile($real_dir,"index.html");
    my $template_content=`cat $index_in`;

    mkdir $real_dir or die "Failed to create $real_dir" unless -d $real_dir;

    !system("cp -rf $template_dir/* $real_dir") or die "Failed to copy templates: $!\n";

    open OUT,'>',$index_out or die "Failed to write to $index_out: $!\n";
    for(split "\n",$template_content)
    {
	if (/<body>/)
	{
	    print OUT "<body onload=\"changeTracks();response_to_select_region();\">\n";

	} else
	{
	    print OUT "$_\n";
	}
	if (/templatemo_main/)
	{
	    print OUT $content,"\n";
	}
    }
    close OUT;
    warn "Index page generated in $real_dir\n";
}
