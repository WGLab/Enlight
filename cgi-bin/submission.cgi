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
my $num_manual_select=$server_conf{'num_manual_region_select'};
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
my $q=new CGI::Pretty;

##################REGION SPECIFICATION HTML CODE##############################
#HTML code for single region specification
my $file_region_spec="<table class='noborder'>
		<tr>
		<td colspan=2>HitSpec format is supported (<a href='http://genome.sph.umich.edu/wiki/LocusZoom#Generating_a_Hit_Spec_File'>help</a>), <br>BUT 7th column and beyond are IGNORED
</td>
<td>
		<input type='file' name='region_file' size=15 />
</td> </tr>
</table>";
my $snp_region_spec="<table class='snp_region_spec'><tr>
		<td>Index SNP</td>
		<td><input type='text' name='refsnp' size=15 /></td>
		</tr>

		<tr>
		<td>Flanking region (kb)</td>
		<td><input type='text' name='snpflank' size=15 value=''/></td>
		</tr></table>";
my $gene_region_spec= "<table class='gene_region_spec'>
                <tr>
		<td>Reference Gene</td>
		<td><input type='text' name='refgene' size=15 /></td>
		</tr>
		<tr>
		<td>Flanking region (kb)</td>
		<td><input type='text' name='geneflank' size=15 value='' /></td>
		<tr>
		<td>Optional Index SNP (default is SNP with lowest P value)</td>
		<td><input type='text' name='refsnp_for_gene' size=15 /></td>
		</tr></table>";
my $chr_region_spec= "<table class='chr_region_spec'>
		<tr>
		<td>Chromosome</td>
		<td><select name='chr' >".
		join ("\n",map { "<option value='$_'>$_</option>" } @chr)
		."</select></td>
		</tr>
		<tr>
		<td>Start (Mb)</td>
		<td><input type='text' name='start' size=15 /></td>
		<tr>
		<td>End (Mb)</td>
		<td><input type='text' name='end' size=15 /></td>
		<tr>
		<td>Optional Index SNP (default is SNP with lowest P value)</td>
		<td><input type='text' name='refsnp_for_chr' size=15 /></td>
		</tr>
</table>";
my $single_region_spec = "<table border=1 class='single_region_spec_head left_aln'>
<tr>
	<td class='region_method_area'>
	    <input type='radio' name='region_method' onclick='response_to_select_region(this)' value='snp' checked >Reference SNP<br>
	     <input type='radio' name='region_method' onclick='response_to_select_region(this)' value='gene'>Reference Gene<br>
	     <input type='radio' name='region_method' onclick='response_to_select_region(this)' value='chr'>Chromosomal Region<br>
	    </td>
</tr>
<tr>
<td class='region_detail_area'>$snp_region_spec $gene_region_spec $chr_region_spec </td>
</tr></table>";
my $multi_region_spec="<table class='noborder'>
<tr>
<td class='multi_region_method_area'>
<input type='radio' name='multi_region_method' onclick='response_to_multi_select_region(this)' value='multi_region'>Manually Specify multi-region<br>
<input type='radio' name='multi_region_method' onclick='response_to_multi_select_region(this)' value='region_file'>Region Spefication File<br>
<tr>
<td class='multi_region_detail_area'><div id='file_region_specification_div_id'>$file_region_spec</div> <div id='multi_manual_region_specification_div_id'><table border=1>".(&gen_multi_manual_select_code($num_manual_select,$single_region_spec))."</table></div></td>
</tr></table>";
###############################END OF REGION SPECIFICATION CODE#######################################	    

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
	var span=document.createElement('span');
	var label=document.createElement('label');
	var upload=document.createElement('input');
	span.title='Drag or use Ctrl, Shift to select multiple files';
	label.innerHTML='Custom track (BED format;.gz okay)';
	upload.type='file';
	upload.name='custom_table';
	upload.multiple='multiple';

	label.appendChild(upload);
	span.appendChild(label);
	col.appendChild(span);
	newrow.appendChild(col);
	insertPos.appendChild(newrow);
    }
}

function response_to_select_region(caller)
{
    var region_spec_container=\$(caller).parentsUntil(\"table.single_region_spec_head\").find(\"td.region_detail_area\");
    if(\$(caller).val()=='snp')
    {
	\$(region_spec_container).find('table.snp_region_spec').show();
	\$(region_spec_container).find('table').not('.snp_region_spec').hide();
    }
    else if (\$(caller).val()=='gene')
    {
	\$(region_spec_container).find('table.gene_region_spec').show();
	\$(region_spec_container).find('table').not('.gene_region_spec').hide();
    }
    else if(\$(caller).val()=='chr')
    {
	\$(region_spec_container).find('table.chr_region_spec').show();
	\$(region_spec_container).find('table').not('.chr_region_spec').hide();
    }
}

function response_to_multi_select_region(caller)
{
    var file_region_spec_container=\$(\"#file_region_specification_div_id\");
    var manual_region_spec_container=\$(\"#multi_manual_region_specification_div_id\");

    if(\$(caller).val()=='region_file')
    {
	\$(file_region_spec_container).show();
	\$(manual_region_spec_container).hide();
    }
    else if(\$(caller).val()=='multi_region')
    {
	\$(manual_region_spec_container).show();
	\$(file_region_spec_container).hide();
	\$(manual_region_spec_container).find(\"table.single_region_spec_head\").each(
		function()
		{
		  var i=\$(this).find(\"td.region_method_area input\").first()
                      i.trigger(\"click\");
		      i.prop('checked',true);
		}
	);
    }
}

//display and hide single region selection and multi-region selection alternatively
function toggle_single_multi_region(caller)
{
    var single_container=\$(\"#region_specification_div_id\");
    var multi_container=\$(\"#multi_region_specification_div_id\");
    if(\$('#region_multi_single_button_single_id').prop('checked'))
    {
	\$(multi_container).hide();
        \$(single_container).show();
	\$(single_container).find(\"td.region_method_area input\").first().trigger(\"click\");
    }
    else if (\$('#region_multi_single_button_multi_id').prop('checked'))
    {
	\$(single_container).hide();
        \$(multi_container).show();
	\$(multi_container).find(\"td.multi_region_method_area input\").first().trigger(\"click\");
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
    document.getElementById('pvalcol_id').value='P';
    document.getElementById('varAnno_id').value='UChicago_eQTL';
    document.getElementById('source_ref_pop_id').value='1000G_March2012,hg19,EUR';	

    \$(\"#region_multi_single_button_single_id\").prop('checked',true);
    \$(\"#region_multi_single_button_multi_id\").prop('checked',false);
    toggle_single_multi_region();

    \$(\"td.region_detail_area input[name='snpflank']\").val(\"20\");
    \$(\"td.region_detail_area input[name='refsnp']\").val(\"rs2071278\");

    document.getElementById('generic_toggle_id').checked=true;
    document.getElementById('anno_toggle_id').checked=true;
    document.getElementById('avinput_id').checked=false;
    document.getElementById('ref_hg19').checked=true;

    //set advanced options
    document.getElementById('ld_toggle_id').checked=true;

    //set interaction options
    \$('#interaction_cell_type_k562_id').prop('checked',true);
    \$('#interaction_cell_type_gm06690_id').prop('checked',false);
    \$('#interaction_type_intra_id').prop('checked',true);
    \$('#interaction_type_intra_id').trigger('click');
    \$('#interaction_type_inter_id').prop('checked',false);
    \$('[name=\"heatmap_toggle\"]').prop('checked',true);


    //clear data track selection
    clear_datatrack_selection();
    document.getElementById('HSMM').checked=true;	
    document.getElementById('K562').checked=true;	
    document.getElementById('HepG2').checked=true;	
    document.getElementById('GM12878').checked=true;	
    document.getElementById('None').checked=true;	

    document.getElementById('TFBS Conservation').checked=true;
    document.getElementById('chromHMM').checked=true;
    document.getElementById('TFBS Region').checked=true;
    changeTracks();

    alert('Example settings loaded.');
}
function loadExampleInput()
{

    \$('#query_example_label_div_id').show();
    \$('#query_hidden_id').val('1');
    \$('#query_file_div_id').hide();

    alert('Example input loaded.');
} 
function hideDetail()
{
    document.getElementById('option_detail_id').style.display='none';
}
function showDetail()
{
    document.getElementById('option_detail_id').style.display='table';
}
function check_before_submission()
{
   if(\$('#query_hidden_id').val() == '0')
   {//we're NOT using example input
    var query_file=\$('#query_file_id').val();
    var query_url=\$('#query_URL_id').val();

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
   }

    //check email

    var email=document.getElementById('email_id').value;
    if (email)
    {
    	var email_pattern=/[\\w\\-\\.]+\\@[\\w\\-\\.]+\\.[\\w\\-\\.]+/;

    	if (! email_pattern.test(email))
    	{
    	    alert('Illegal email address!');
    	    return false;
    	}
    } else
    {
    //when multiple regions are specified, the job will take a while
    //user should provide email
        if(\$(\"#region_multi_single_button_multi_id\").prop('checked'))
        {
            alert('Email must be provided when multiple regions are to be plotted');
            return false;
        }
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
    var col_pat=/[^\\w\\-]/;

    if (col_pat.test(p_val) || col_pat.test(marker))
    {
	alert('Only letters, numbers, dashes, underscores are allowed in column name.');
	return false;
    }

    //check datatracks
    var generic_toggle=document.getElementById('generic_toggle_id').checked;
    var anno_toggle=document.getElementById('anno_toggle_id').checked;
    var datatrack=\$('[name=\"generic_table\"]').filter(':checked');
    var custom_table=document.getElementsByName('custom_table');
    var custom_table_count=0;
    \$(custom_table).each(function(){
		    custom_table_count+=this.files.length;
		    });

    if ( generic_toggle || anno_toggle )
    {
	if (datatrack.length==0 && custom_table_count==0)
	{
	    alert (\"No annotation data tracks selected or uploaded \\nwhile generic plot or annotation is enabled.\");
	    return false;
	}
    }
    if ( datatrack.length+custom_table_count>$generic_table_max)
    {
	alert('Too many data tracks (max: $generic_table_max)');
	return false;
    }


    //region specification
    var region_pat=/[ \\\$\\t\\r\\n\\*\\|\\?\\>\\<\\'\\\"\\,\\;\\:\\[\\]\\{\\}]/;
    var region_method;
    var return_value=true;
    var at_least_one=false;
    
    //when toggled to multi view, the value of toggler is single and vice versa
    if (\$('#region_multi_single_button_multi_id').prop('checked'))
    {
    	region_method=\$('#multi_region_specification_div_id').find(\"input[name^='region_method']:checked\");//select input elements with name starting with region_method
    }
    else if (\$('#region_multi_single_button_single_id').prop('checked'))
    {
    	region_method=\$('#region_specification_div_id').find(\"input[name^='region_method']:checked\");//select input elements with name starting with region_method
    }
    
    //user must either upload a region specification file
    //or specify region for each region specification table

	if(! \$(\"input[name='region_file']\").val() )
	{
		\$(region_method).each(
				function() {
				var region_spec_container=\$(this).parentsUntil(\"table.single_region_spec_head\").find(\"td.region_detail_area\");
				var refsnp=\$(region_spec_container).find(\"input[name^='refsnp']\").val();
				var snpflank=\$(region_spec_container).find(\"input[name^='snpflank']\").val();
				var refgene=\$(region_spec_container).find(\"input[name^='refgene']\").val();
				var geneflank=\$(region_spec_container).find(\"input[name^='geneflank']\").val();
				var generefsnp=\$(region_spec_container).find(\"input[name^='refsnp_for_gene']\").val();
				var chr=\$(region_spec_container).find(\"select[name^='chr']\").val();
				var start=\$(region_spec_container).find(\"input[name^='start']\").val();
				var end=\$(region_spec_container).find(\"input[name^='end']\").val();
				var chrrefsnp=\$(region_spec_container).find(\"input[name^='refsnp_for_chr']\").val();

					if (\$(this).val() == 'snp')
					{	
						if ( (refsnp.length!=0 && snpflank.length==0) || (refsnp.length==0 && snpflank.length!=0) )
						{
							alert('Both reference SNP and flanking region must be supplied.');
							return_value=false;
							return false;//stop each iteration
						} else if (region_pat.test(refsnp) || region_pat.test(snpflank))
						{
							alert(\"Illegal characters found in reference SNP or flanking regin\\nPlease remove \$ \' \\\" \{ \} \[ \] \\\\ \> \< \: \; \, \* \| and tab, space, newline.\");
							return_value=false;
							return false;
						}	
						if( refsnp.length!=0 && snpflank.length!=0)
						{
							at_least_one=true;
						}
					} else if (\$(this).val() == 'gene')
					{
						if ( (refgene.length!=0 && geneflank.length==0) || (refgene.length==0 && geneflank.length!=0) )
						{
							alert('Both reference gene and flanking region must be supplied.');
							return_value=false;
							return false;
						} else if (region_pat.test(refgene) || region_pat.test(geneflank) || region_pat.test(generefsnp))
						{
							alert(\"Illegal characters found in reference SNP or flanking regin\\nPlease remove \$ \' \\\" \{ \} \[ \] \\\\ \> \< \: \; \, \* \| and tab, space, newline.\");
							return_value=false;
							return false;
						}	
						if( refgene.length!=0 && geneflank.length!=0)
						{
							at_least_one=true;
						}
					} else if (\$(this).val() == 'chr')
					{
						if ( (start.length!=0 && end.length==0) || (start.length==0 && end.length!=0) )
						{
							alert('Both chromosome start and end must be supplied');
							return_value=false;
							return false;
						} else if (region_pat.test(chr) || region_pat.test(start) || region_pat.test(end) || region_pat.test(chrrefsnp))
						{
							alert(\"Illegal characters found in reference SNP or flanking regin\\nPlease remove \$ \' \\\" \{ \} \[ \] \\\\ \> \< \: \; \, \* \| and tab, space, newline.\");
							return_value=false;
							return false;
						}	
						if( start.length!=0 && end.length!=0)
						{
							at_least_one=true;
						}
					}
			}
		);
		if(!at_least_one && return_value)
		{
			//when return_value is false, an alert has been issued, no need to give more alerts
			alert('No region is specified!');
		}
		return return_value&&at_least_one;
	} else
	{
		return true;
	}
}
";

################html generation###############
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
$page.= $q->p("$intro<br><br>");
$page.= $q->start_form(-name=>'main',-action=>"/cgi-bin/process.cgi",-method=>"post",-onSubmit=>"return check_before_submission();");
$page.= $q->h2("Input");
$page.= $q->table(
    {-border=>0},
    $q->Tr(
	$q->td("DEMO<br>
	        <a href='pages/example/exampleinput.html'>(example input)</a><br>
		<a href='pages/example/exampleoutput/index.html'>(example output)</a>"),
	$q->td("<button type='button' onclick='loadExampleSetting()'>Load settings for example input</button>
	    <br>
	    <button type='button' onclick='loadExampleInput()'>Load example input</button>"),
    ),
    $q->Tr(
	$q->td("<span title='receive result link'>Email (mandatory for multi-region)</span>"),
	$q->td("<input name='email' id='email_id' type='email' onclick=\"this.value=''\" />"),
    ),
    $q->Tr(
	$q->td("Input file (1st line is header; .gz okay)"),
	$q->td({-id=>'query_cell_id'},
		$q->div({id=>'query_file_div_id'},
			$q->filefield(-id=>"query_file_id",-name=>"query"),
			"</br>or paste URL","<input name='query_URL' type='url' id='query_URL_id' />"
		       ),
		"<input id='query_hidden_id' type='hidden' name='example_upload' value=''/>",
		"<div id='query_example_label_div_id' style='display:none'><label id='query_example_label'>Example input loaded</label></div>"
	      ),
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
	$q->td(	["Genome Build",
                '<label>
		<input type="radio" name="ref" value="hg18">hg18
		</label>
		<label>
		<input type="radio" name="ref" id="ref_hg19" value="hg19" checked="checked">hg19
		</label>']
	),
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


#########################START OF REGION SPECIFICATION SECTION#########################################
$page.="<br> <br>\n";
$page.= $q->h2("<span title='plot region'>Specify a region</span>");
$page.= $q->div($q->table({-class=>'noborder'},
			$q->Tr($q->td(
		'<label>
		<input type="radio" name="region_multi_single_button" id="region_multi_single_button_multi_id" value="multi" onclick="toggle_single_multi_region();" >multiple
		</label>
		<input type="radio" name="region_multi_single_button" id="region_multi_single_button_single_id" checked="checked" value="single" onclick="toggle_single_multi_region();" >single
		</label>'),
			      ),
			$q->Tr($q->td(
					"<div id='region_specification_div_id' style='display:none'>$single_region_spec</div><div style='display:none' id='multi_region_specification_div_id'> $multi_region_spec</div>"),
			      ),
			));
##############################END OF REGION SPECIFICATION SECTION####################################
$page.="<br> <br>\n";
$page.= $q->h2("<span title='Plot HiC interaction heatmap'>HiC interaction plot</span>");
$page.= $q->table( {-border=>1},
    $q->Tr(
	$q->td( {-colspan=>2},
	    "<span title='Do you want an HiC interaction heatmap plot?'>".
	    $q->checkbox(-name=>'heatmap_toggle',-id=>'heatmap_toggle_id',-checked=>1,-label=>'Output interaction heatmap?').
	    "</span>"
	), #return 'on' if checked
    ),
    $q->Tr(
	$q->td( ["Interaction type (resolution)",
		'<label>
		<input type="radio" name="interaction_type" id="interaction_type_inter_id" value="interchromosomal" '."onclick=\"\$('#interaction_chr_tr_id').show();\"".' >INTERchromosomal(1Mb)
		</label><br>
		<input type="radio" id="interaction_type_intra_id" name="interaction_type" value="intrachromosomal" '."onclick=\"\$('#interaction_chr_tr_id').hide();\"".' checked="checked">INTRAchromosomal(100Kb)
		</label>'
	    ]
	),
    ),
    $q->Tr(
	$q->td( ["Cell lines",
		'<label>
		<input type="radio" name="interaction_cell_type" id="interaction_cell_type_k562_id" value="k562" >K562
		</label>
		<input type="radio" name="interaction_cell_type" id="interaction_cell_type_gm06690_id" value="gm06690" checked="checked">GM06690
		</label>'
	    ]
	),
    ),
    $q->Tr({id=>'interaction_chr_tr_id',style=>'display:none'},
	$q->td(["Chromosome","<select name='interaction_chr' >".
		join ("\n",map { "<option value='$_'>$_</option>" } @chr)
		."</select>"]),
    ),
);

$page.="<br> <br>\n";
$page.= $q->h2("<span title='show signal strengths in regions'>Generic plot (using UCSC BED tables)</span>");
$page.= $q->table( {-class=>'noborder'},
    $q->Tr(
	$q->td( {-colspan=>2},
	    "<span title='Do you want a generic (annotation) plot?'>".
	    $q->checkbox(-name=>'generic_toggle',-id=>'generic_toggle_id',-checked=>1,-label=>'Generic plot?').
	    "</span>"
	), #return 'on' if checked
    ),
    $q->Tr(
	$q->td({-colspan=>2},"<span title='Do you want text annotation?'>".
	    $q->checkbox(-name=>'anno_toggle',-id=>'anno_toggle_id',-checked=>0,-label=>'Output ANNOVAR annotation?').
	    "</span>"
	),
    ),
    $q->Tr(
	$q->td({-colspan=>2},"<span title='First 5 columns correspond to chromosome,start,end,alternative allele,reference allele'>".
	    $q->checkbox(-name=>'avinput',-id=>'avinput_id',-checked=>0,-label=>'Input file in ANNOVAR format?').
	    "</span>"
	),
    ),
    #LD output function temporily disabled because there could be multiple regions
    $q->Tr(
        $q->td( ["Advanced options",
        	'<label>
        	<input type="radio" name="detail_toggle" value="show" onclick="showDetail()">show
        	</label>
        	<input type="radio" name="detail_toggle" value="hide" onclick="hideDetail()" checked="checked">hide
        	</label>'
            ]
        ),
    ),
);
$page.= $q->table({-class=>'advanced',-id=>'option_detail_id',-style=>'display:none'},
    $q->Tr(
	[$q->td(
	    $q->checkbox(-name=>'ld_toggle',-id=>'ld_toggle_id',-checked=>1,-label=>'Output linkage disequilibrium (only works with SINGLE region, written in input file)')
	),
	#$q->td(
	#	"<p>LD breakdown in summary plot (separated by comma, mininum 0, maximum 1)</p>
	#	<input type='text' name='ld_breakdown' id='ld_breakdown_id' value='/>
	#	"
	#),
	#$q->td(

	#),
	#$q->td(

	#),
	]
    ),
);
$page.= "</br></br>";
$page.= $q->p({-class=>'center'},"<b>Please upload your own files <b style=\"color:red\">AFTER</b> selecting data tracks.</b><br>");
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
	    print OUT "<body onload=\"changeTracks();toggle_single_multi_region();\">\n";

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
#generate html code for manual multiple region selection (n is number of cells, unit is the content for each cell)
sub gen_multi_manual_select_code
{
    my $n=shift;
    my $unit=shift;
    my $cell_per_line=3;
    my $s='';
    my $lines=int($n/$cell_per_line);
    my $cells=$n % $cell_per_line;
    my $i=0;
    my $num_button_group=3;
    my $j=$num_button_group; #number of buttons per group, buttons within same group have identical name
    $s.=("<tr>".("<td>$unit</td>"x$cell_per_line)."</tr>")x$lines if $lines>0;
    $s.="<tr>".("<td>$unit</td>"x$cells)."</tr>" if $cells>0;

    #make some elements used in post-processing distinguishable by name
    $s=~s/\bregion_method\b/"region_method".($j==1? ($j=$num_button_group,$i++):($j--,$i))/eg;
    for my $item("refsnp","snpflank","refgene","geneflank","refsnp_for_gene","chr","start","end","refsnp_for_chr")
    {
	$j=$num_button_group;
	$i=0;
	$s=~s/name='$item\b/"name='$item".($i++)/eg;
    }
    return $s;
}
sub rm_newline
{
my $s=shift;
$s=~s/\n//mg;
return $s;
}
