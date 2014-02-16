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


my $intro="Enlight draws regional plots for GWAS results, and overlays epigenetic modification, DNase sensitivity site, transcription factor binding annotation onto it. The combined plot will help identify causal variants. Users can also upload custom annotation, obtain text annotation for each SNP.";
#read global configurations
my %server_conf=&Utils::readServConf(File::Spec->catfile($RealBin,"../conf/enlight_server.conf"))
    or die "Reading server configuration file failed!\n";

#read list of available locuszoom databases
my $flank_default=$server_conf{"flank_default"} || "200";
my $generic_table_max=$server_conf{"generic_table_max"} || 10;
my $admin_email=$server_conf{'admin'};
my $trackList=$server_conf{'trackList'} or die "Failed to read datatrack list setting\n";
my $varAnnoList=$server_conf{'varAnnoList'} or die "Failed to read variant annotation list settings\n";
my $cellDesc=$server_conf{'cellDesc'} or die "Failed to read cell description\n";
my $expDesc=$server_conf{'expDesc'} or die "Failed to read experiment description\n";
#my $public_key=$server_conf{'public_key'} or die "No public key for reCAPTCHA\n";

my @ref=('hg18','hg19');
my $ref_default='hg19';
my %ref_label=('hg19'=>'hg19','hg18'=>'hg18');

my @source_ref_pop= sort (map {$server_conf{$_}} grep { /^\d+$/ } (keys %server_conf) ); #/^\d/ since only keys are numeric, first one will be default
my %source_ref_pop_label=map {($_,$_)} @source_ref_pop; 
my ($default_source_ref_pop)=grep {/$ref_default/ and /EUR/i} @source_ref_pop;

my %tracks=&Utils::readObj($trackList);
my %cell= map { ($tracks{$_}{cell},$tracks{$_}{table}) } keys %tracks;
my %experiment= map { ($tracks{$_}{experiment},$tracks{$_}{table}) } keys %tracks;
my %cell_desc= &tab2hash($cellDesc);
my %exp_desc= &tab2hash($expDesc);

my @varAnno=sort (split /,/,$varAnnoList);
push @varAnno,'NULL';
my %varAnno_label=map {($_,$_)} @varAnno;

my @qformat=("whitespace","tab","space","comma");
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

    //remove all child nodes while saving custom uploads info
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

    var radio_group=document.getElementsByName('region_method');
    var input_value=getCheckedRadio(radio_group).value;

    if (input_value=='snp')
    {
	document.getElementById('snp_region_specify').style.display='block';
	document.getElementById('gene_region_specify').style.display='none';
	document.getElementById('chr_region_specify').style.display='none';
    } else if (input_value=='gene')
    {
	document.getElementById('gene_region_specify').style.display='block';
	document.getElementById('chr_region_specify').style.display='none';
	document.getElementById('snp_region_specify').style.display='none';
    } else if (input_value=='chr')
    {
	document.getElementById('gene_region_specify').style.display='none';
	document.getElementById('chr_region_specify').style.display='block';
	document.getElementById('snp_region_specify').style.display='none';
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
    document.getElementById('varAnno_id').value='GTEx_eQTL_11162013';
    document.getElementById('source_ref_pop_id').value='1000G_March2012,hg19,EUR';	
    document.getElementById('region_method_snp').checked=true;
    response_to_select_region();

    document.getElementById('refsnp_id').value='rs10318';
    document.getElementById('snp_flank_region').value='50';
    document.getElementById('generic_toggle_id').checked=true;
    document.getElementById('anno_toggle_id').checked=true;
    document.getElementById('avinput_id').checked=false;
    document.getElementById('ref_hg19').checked=true;

    //clear data track selection
    clear_datatrack_selection();
    document.getElementById('Caco-2').checked=true;	
    document.getElementById('HCT116').checked=true;	
    document.getElementById('HepG2').checked=true;	
    document.getElementById('DNase-seq').checked=true;
    document.getElementById('chromHMM').checked=true;
    changeTracks();

    alert('Example settings loaded.');
}
function loadExampleInput()
{
    var query_cell=document.getElementById('query_cell_id');
    var label=document.createElement('label');
    var hiddenInput=document.createElement('input');

    while(query_cell.firstChild)
    {
	query_cell.removeChild(query_cell.firstChild);
    }

    label.innerHTML='Example Input loaded';
    hiddenInput.type='hidden';
    hiddenInput.name='example_upload';
    hiddenInput.value='1';

    query_cell.appendChild(label);
    query_cell.appendChild(hiddenInput);
    alert('Example input loaded.');
} 
function check_before_submission()
{
    var query_file=document.getElementById('query_file_id').value;
    var query_url=document.getElementById('query_URL_id').value;

    if (query_file.length>0 && query_url.length>0)
    {
	alert('Input URL cannot be used with input file!');
	//abort submission
	return false;
    }

    if (query_file.length==0 && query_url.length==0)
    {
	alert('No input!');
	return false;
    }

    //check email

    var email=document.getElementById('email_id').value;
    var email_pattern=/[\\w\\-\\.]+\\@[\\w\\-\\.]+\\.[\\w\\-\\.]+/;

    if (! email_pattern.test(email))
    {
	alert('Illegal email address!');
	return false;
    }

    //check genome build
    var ref=document.getElementById('ref_hg19').checked;
    var ref_ld=document.getElementById('source_ref_pop_id').value.split(',');
    ref_ld=ref_ld[1];

    if (ref)
    {
	ref='hg19';
    } else
    {
	ref='hg18';
    }

    if (ref != ref_ld)
    {
	alert('Reference genome does not match source population');
	return false;
    }

    //check marker column
    var marker=document.getElementById('markercol_id').value;

    if (marker.length==0)
    {
	alert('Marker column name is empty!');
	return false;
    }

    //check P value column
    var p_val=document.getElementById('pvalcol_id').value;

    if (p_val.length==0)
    {
	alert('P value column name is empty!');
	return false;
    }

    //Only letters, numbers, dashes, underscores are allowed in column name
    var col_pat=/[\\W\\-]/;

    if (col_pat.test(p_val) || col_pat.test(marker))
    {
	alert('Only letters, numbers, dashes, underscores are allowed in column name.');
	return false;
    }

    //check datatracks
    var generic_toggle=document.getElementById('generic_toggle_id').value;
    var anno_toggle=document.getElementById('anno_toggle_id').value;
    var datatrack=document.getElementsByName('generic_table');
    var custom_table=document.getElementsByName('custom_table');
    //remove empty elements
    custom_table=Array.prototype.filter.call(custom_table,function(x) {return x.value});

    if ( generic_toggle || anno_toggle )
    {
	if (datatrack.length==0 && custom_table.length==0)
	{
	    alert (\"No annotation data tracks selected or uploaded \\nwhile generic plot or annotation is enabled.\");
	    return false;
	}
    }
    if ( datatrack.length+custom_table.length>$generic_table_max)
    {
	alert('Too many data tracks (max: $generic_table_max)');
	return false;
    }


    //region specification
    var region_pat=/[ \\\$\\t\\r\\n\\*\\|\\?\\>\\<\\'\\\"\\,\\;\\:\\[\\]\\{\\}]/;
    var region_method=document.getElementsByName('region_method');

    var refsnp=document.getElementById('refsnp_id').value;
    var snpflank=document.getElementById('snp_flank_region').value;
    var refgene=document.getElementById('refgene_id').value;
    var geneflank=document.getElementById('geneflank_id').value;
    var generefsnp=document.getElementById('refsnp_for_gene_id').value;
    var chr=document.getElementById('chr_id').value;
    var start=document.getElementById('start_id').value;
    var end=document.getElementById('end_id').value;
    var chrrefsnp=document.getElementById('refsnp_for_chr_id').value;

    if (region_method[0].value == 'snp')
    {
    	if ( refsnp.length==0 || snpflank.length==0)
    	{
    		alert('No reference SNP or flanking region');
    		return false;
    	} else if (region_pat.test(refsnp) || region_pat.test(snpflank))
    	{
    		alert(\"Illegal characters found in reference SNP or flanking regin\\nPlease remove \$ \' \\\" \{ \} \[ \] \\\\ \> \< \: \; \, \* \| and tab, space, newline.\");
    		return false;
    	}	
    } else if (region_method[0].value == 'gene')
    {
    	if ( refgene.length==0 || geneflank.length==0)
   	{
   		alert('No reference gene or flanking region');
   		return false;
   	} else if (region_pat.test(refgene) || region_pat.test(geneflank) || region_pat.test(generefsnp))
   	{
   		alert(\"Illegal characters found in reference SNP or flanking regin\\nPlease remove \$ \' \\\" \{ \} \[ \] \\\\ \> \< \: \; \, \* \| and tab, space, newline.\");
   		return false;
   	}	
    } else if (region_method[0].value == 'chr')
    {
    	if ( chr.length==0 || start.length==0 || end.length==0)
    	{
    		alert('No chromosome name or start or end');
    		return false;
    	} else if (region_pat.test(chr) || region_pat.test(start) || region_pat.test(end) || region_pat.test(chrrefsnp))
    	{
    		alert(\"Illegal characters found in reference SNP or flanking regin\\nPlease remove \$ \' \\\" \{ \} \[ \] \\\\ \> \< \: \; \, \* \| and tab, space, newline.\");
    		return false;
    	}	
    }
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
$page.= $q->h2("Introduction");
$page.= $q->p("$intro<br /><br />");
$page.= $q->start_form(-name=>'main',-action=>"/cgi-bin/process.cgi",-method=>"post",-onSubmit=>"return check_before_submission();");
$page.= $q->h2("Input");
$page.= $q->table(
    {-border=>0},
    $q->Tr(
	$q->td("DEMO<br /><a href='/example/rs10318.txt'>(example file)</a>"),
	$q->td("<button type='button' onclick='loadExampleSetting()'>Load settings for example input</button>
	    <br />
	    <button type='button' onclick='loadExampleInput()'>Load example input</button>"),
    ),
    $q->Tr(
	$q->td("<span title='receive result link'>Email (optional)</span>"),
	$q->td("<input name='email' id='email_id' type='email' onclick=\"this.value=''\" />"),
    ),
    $q->Tr(
	$q->td("Input file (first line must be header)"),
	$q->td({-id=>'query_cell_id'},$q->filefield(-id=>"query_file_id",-name=>"query"),"</br></br>or paste URL","<input name='query_URL' type='url' id='query_URL_id' />"),
    ),
    $q->Tr(
	$q->td("Field delimiter"),
	$q->td($q->radio_group(-name=>"qformat",-id=>"qformat_whitespace",-values=>\@qformat,-labels=>\%qformat_label,-default=>$qformat_default)),
    ),
    $q->Tr(
	$q->td("<span title='this columns contains rsID'>Marker Column (case sensitive)</span>"),
	$q->td($q->textfield(-name=>'markercol',-id=>'markercol_id',-default=>'', -onclick=>"this.value=''")),
    ),
    $q->Tr(
	$q->td("P value column (case-sensitive)"),
	$q->td($q->textfield(-name=>"pvalcol",-id=>'pvalcol_id',-default=>'', -onclick=>"this.value=''")),
    ),
    $q->Tr(
	$q->td("<span title='choose data set for computing Linkage Disequilibrium'>Genome Build/LD source/Population</span>"),
	$q->td(
	    $q->popup_menu(-name=>'source_ref_pop',-id=>'source_ref_pop_id',-values=> \@source_ref_pop,-labels=>\%source_ref_pop_label,-default=>[$default_source_ref_pop])
	),
    ),
    $q->Tr(
	$q->td("<span title='show if a variant appears in a particular database'>Mark variants in database: </span>"),
	$q->td(
	    $q->popup_menu(-name=>'varAnno',-id=>'varAnno_id',-values=> \@varAnno,-labels=>\%varAnno_label,-default=>['NULL'])
	),
    ),
);

$page.="<br /> <br />\n";
$page.= $q->h2("<span title='plot region'>Specify a region</span>");
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
	    $q->table( {-id=>'snp_region_specify',-style=>'display:none'},
		"<tr>
		<td>Index SNP</td>
		<td><input type='text' name='refsnp' id='refsnp_id' onclick=\"this.value=''\"/></td>
		</tr>

		<tr>
		<td>Flanking region (kb)</td>
		<td><input type='text' name='snpflank' id='snp_flank_region' onclick=\"this.value=''\" value='$flank_default'/></td>
		</tr>"
	    ),

	    $q->table( {-id=>'gene_region_specify',-style=>'display:none;'},
		"<tr>
		<td>Reference Gene</td>
		<td><input type='text' name='refgene' id='refgene_id' onclick=\"this.value=''\"/></td>
		</tr>
		<tr>
		<td>Flanking region (kb)</td>
		<td><input type='text' name='geneflank' id='geneflank_id' onclick=\"this.value=''\" value='$flank_default' /></td>
		<tr>
		<td>Optional Index SNP (default is SNP with lowest P value)</td>
		<td><input type='text' name='refsnp_for_gene' id='refsnp_for_gene_id' onclick=\"this.value=''\" /></td>
		</tr>"),

	    $q->table( {-id=>'chr_region_specify',-style=>'display:none;'},
		"<tr>
		<td>Chromosome</td>
		<td><select name='chr' id='chr_id'>
		<option value='1'>1</option>
		<option value='2'>2</option>
		<option value='3'>3</option>
		<option value='4'>4</option>
		<option value='5'>5</option>
		<option value='6'>6</option>
		<option value='7'>7</option>
		<option value='8'>8</option>
		<option value='9'>9</option>
		<option value='10'>10</option>
		<option value='11'>11</option>
		<option value='12'>12</option>
		<option value='13'>13</option>
		<option value='14'>14</option>
		<option value='15'>15</option>
		<option value='16'>16</option>
		<option value='17'>17</option>
		<option value='18'>18</option>
		<option value='19'>19</option>
		<option value='20'>20</option>
		<option value='21'>21</option>
		<option value='22'>22</option>
		<option value='X'>X</option>
		</select></td>
		</tr>
		<tr>
		<td>Start (Mb)</td>
		<td><input type='text' name='start' id='start_id' onclick=\"this.value=''\"/></td>
		<tr>
		<td>End (Mb)</td>
		<td><input type='text' name='end' id='end_id' onclick=\"this.value=''\"/></td>
		<tr>
		<td>Optional Index SNP (default is SNP with lowest P value)</td>
		<td><input type='text' name='refsnp_for_chr' id='refsnp_for_chr_id' onclick=\"this.value=''\"/></td>
		</tr>"),
	),
    ),
);

$page.="<br /> <br />\n";
$page.= $q->h2("<span title='show signal strengths in regions'>Generic plot (using UCSC BED tables)</span>");
$page.= $q->table( {-class=>'noborder'},
    $q->Tr(
	$q->td(
	    "<span title='Do you want a generic (annotation) plot?'>".
	    $q->checkbox(-name=>'generic_toggle',-id=>'generic_toggle_id',-checked=>1,-label=>'Generic plot?').
	    "</span>"
	), #return 'on' if checked
    ),
    $q->Tr(
	$q->td("<span title='Do you want text annotation?'>".
	    $q->checkbox(-name=>'anno_toggle',-id=>'anno_toggle_id',-checked=>0,-label=>'Output ANNOVAR annotation?').
	    "</span>"
	),
    ),
    $q->Tr(
	$q->td("<span title='First 5 columns correspond to chromosome,start,end,alternative allele,reference allele'>".
	    $q->checkbox(-name=>'avinput',-id=>'avinput_id',-checked=>0,-label=>'Input file in ANNOVAR format?').
	    "</span>"
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
$page.= $q->p({-class=>'center'},"<b>Please upload your own files AFTER selecting data tracks.</b><br />");
$page.= $q->table(
    $q->Tr(
	$q->th(["Cell Line",
	    "Experiment Type",
	    "Data Tracks (max: $generic_table_max; <a class='button' href=\"/example/example.bed\"><strong>BED Example</strong></a>)"]),
    ),
    $q->Tr(
	$q->td( {-class=>'table_align'},
	    $q->table( {-class=>'noborder left_aln'},
		$q->Tr([
		    map { 

			$q->td("<span title='$cell_desc{$_}'>". 
			    $q->checkbox( {-id=>$_,-class=>'cell',-label=>$_,-checked=>0,-value=>$_,-onchange=>'changeTracks()',} )."</span>"
			); 
		    } sort keys %cell
		    ]),
	    )
	),
	$q->td( {-class=>'table_align'},
	    $q->table( {-class=>'noborder left_aln'},
		$q->Tr([
		    map { 

			$q->td("<span title='$exp_desc{$_}'>".
			    $q->checkbox( {-id=>$_,-class=>'experiment',-label=>$_,-checked=>0,-value=>$_,-onchange=>'changeTracks()',} )."</span>"
			);
		    } sort keys %experiment
		    ]),
	    )
	),
	$q->td( {-class=>'table_align'},
	    $q->table( {-class=>'noborder left_aln',-id=>'dataTrackHere'}, $q->p("")),
	),
    ),
);

$page.= $q->table( {-class=>'noborder'},
    $q->Tr(
	$q->td(
	    $q->p($q->submit("Submit"),$q->reset())
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
sub tab2hash
{
    my $in=shift;
    my %hash;

    open IN,'<',$in or die "Failed to read $in: $!\n";
    while(<IN>)
    {
	my @f=split /\t/,$_,-1;
	die "At least 2 fields expected at line $. of $in: @f\n" unless @f>=2;
	$hash{$f[0]}=$f[1];
    }
    close IN;
    return %hash;
}
