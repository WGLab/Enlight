<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>Enlight</title>
<meta name="keywords" content="green jelly, theme, free templates, nivo image slider, website, templatemo, CSS, HTML" />
<meta name="description" content="Green Jelly Theme, free CSS template provided by templatemo.com" />
<link href="css/templatemo_style.css" rel="stylesheet" type="text/css" />

<link rel="stylesheet" href="css/nivo-slider.css" type="text/css" media="screen" />

<script language="javascript" type="text/javascript">
function clearText(field)
{
    if (field.defaultValue == field.value) field.value = '';
    else if (field.value == '') field.value = field.defaultValue;
}
</script>
<script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
    (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
      m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
        })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

  ga('create', 'UA-50646209-1', 'usc.edu');
    ga('send', 'pageview');

</script>

<link rel="stylesheet" type="text/css" href="css/ddsmoothmenu.css" />

<script type="text/javascript" src="js/jquery.min.js"></script>
<script type="text/javascript" src="js/ddsmoothmenu.js">

/***********************************************
* Smooth Navigational Menu- (c) Dynamic Drive DHTML code library (www.dynamicdrive.com)
* This notice MUST stay intact for legal use
* Visit Dynamic Drive at http://www.dynamicdrive.com/ for full source code
***********************************************/

</script>

<script type="text/javascript">

ddsmoothmenu.init({
	mainmenuid: "templatemo_menu", //menu DIV id
	orientation: 'h', //Horizontal or vertical menu: Set to "h" or "v"
	classname: 'ddsmoothmenu', //class added to menu's outer DIV
	//customtheme: ["#1c5a80", "#18374a"],
	contentsource: "markup" //"markup" or ["container_id", "path_to_menu_file"]
})

</script>
<script>
$(document).ready(function(){
		changeTracks();
		$('#region_multi_single_button_id').click(toggle_single_multi_region());
		});
</script>
  
</head>
<body>

<div id="templatemo_wrapper">
	<div id="templatemo_header"></div> <!-- end of header -->
      <div id="templatemo_menu" class="ddsmoothmenu">
        <ul>
            <li><a href="index.html" class="selected">Home</a></li>
            <li><a href="pages/tutorial.html">Tutorial</a></li>
            <li><a href="pages/help.html">Help</a></li>
            <li><a href="pages/pipeline.html">Pipeline</a> </li>
            </ul>
        <br style="clear: left" />
    </div> <!-- end of menu -->
    
    <div id="templatemo_slider_wrapper">
      <div id="htmlcaption" class="nivo-html-caption">
       	  <strong>This</strong> is an example of a HTML caption with <a href="#">a link</a>.
        </div>
    
    </div>
    
    <script type="text/javascript" src="js/jquery-1.4.3.min.js"></script>
    <script type="text/javascript" src="js/jquery.nivo.slider.js"></script>
    <script type="text/javascript">
    $(window).load(function() {
    $('#slider').nivoSlider();
    });
    </script>
    
    <div id="templatemo_main"><br class="cleaner" />
<script type="text/javascript"> //<![CDATA[

function changeTracks()
{
    var insertPos=document.getElementById('dataTrackHere');
    var all=[ {name:'wgEncodeBroadHistoneH1hescH3k9acStdPk',cell:'H1-hESC',experiment:'ChIP-seq_H3K9ac'},
{name:'wgEncodeBroadHmmGm12878HMM',cell:'GM12878',experiment:'chromHMM'},
{name:'wgEncodeBroadHistoneNhekH3k9acStdPk',cell:'NHEK',experiment:'ChIP-seq_H3K9ac'},
{name:'wgEncodeBroadHmmHuvecHMM',cell:'HUVEC',experiment:'chromHMM'},
{name:'wgEncodeBroadHistoneA549H3k04me3Etoh02Pk',cell:'A549',experiment:'ChIP-seq_H3K4me3'},
{name:'wgEncodeSydhTfbsHelas3Tcf7l2UcdPk',cell:'HeLa-S3',experiment:'ChIP-seq_TCF7L2'},
{name:'wgEncodeHaibMethylRrbsH1hescHaibSitesRep1',cell:'H1-hESC',experiment:'methyl RRBS'},
{name:'wgEncodeBroadHistoneHuvecH3k79me2Pk',cell:'HUVEC',experiment:'ChIP-seq_H3K79me2'},
{name:'wgEncodeHaibMethylRrbsHepg2DukeSitesRep1',cell:'HepG2',experiment:'methyl RRBS'},
{name:'wgEncodeBroadHistoneNhlfH3k79me2Pk',cell:'NHLF',experiment:'ChIP-seq_H3K79me2'},
{name:'wgEncodeBroadHistoneHsmmH3k27acStdPk',cell:'HSMM',experiment:'ChIP-seq_H3K27ac'},
{name:'wgEncodeBroadHmmHepg2HMM',cell:'HepG2',experiment:'chromHMM'},
{name:'wgEncodeBroadHistoneNhekH3k27me3StdPk',cell:'NHEK',experiment:'ChIP-seq_H3K27me3'},
{name:'wgEncodeBroadHistoneNhlfH3k27me3StdPk',cell:'NHLF',experiment:'ChIP-seq_H3K27me3'},
{name:'wgEncodeBroadHistoneHsmmH3k27me3StdPk',cell:'HSMM',experiment:'ChIP-seq_H3K27me3'},
{name:'wgEncodeBroadHistoneNhlfH3k4me3StdPk',cell:'NHLF',experiment:'ChIP-seq_H3K4me3'},
{name:'wgEncodeUwTfbsCaco2CtcfStdPkRep1',cell:'Caco-2',experiment:'ChIP-seq_CTCF'},
{name:'wgEncodeBroadHistoneHuvecH3k4me1StdPk',cell:'HUVEC',experiment:'ChIP-seq_H3K4me1'},
{name:'wgEncodeOpenChromDnaseA549Pk',cell:'A549',experiment:'DNase-seq'},
{name:'wgEncodeBroadHistoneGm12878H3k36me3StdPk',cell:'GM12878',experiment:'ChIP-seq_H3K36me3'},
{name:'wgEncodeBroadHistoneNhlfH3k9acStdPk',cell:'NHLF',experiment:'ChIP-seq_H3K9ac'},
{name:'wgEncodeSydhHistoneMcf7H3k27me3bUcdPk',cell:'MCF-7',experiment:'ChIP-seq_H3K27me3'},
{name:'wgEncodeSydhHistoneMcf7H3k09me3UcdPk',cell:'MCF-7',experiment:'ChIP-seq_H3K9me3'},
{name:'wgEncodeBroadHistoneHsmmH3k4me1StdPk',cell:'HSMM',experiment:'ChIP-seq_H3K4me1'},
{name:'wgEncodeBroadHistoneK562H3k4me3StdPk',cell:'K562',experiment:'ChIP-seq_H3K4me3'},
{name:'wgEncodeBroadHistoneH1hescH3k36me3StdPk',cell:'H1-hESC',experiment:'ChIP-seq_H3K36me3'},
{name:'wgEncodeBroadHistoneH1hescH3k27me3StdPk',cell:'H1-hESC',experiment:'ChIP-seq_H3K27me3'},
{name:'wgEncodeBroadHistoneHsmmH3k36me3StdPk',cell:'HSMM',experiment:'ChIP-seq_H3K36me3'},
{name:'wgEncodeBroadHistoneHmecH3k27me3StdPk',cell:'HMEC',experiment:'ChIP-seq_H3K27me3'},
{name:'wgEncodeBroadHistoneHelas3H3k27acStdPk',cell:'HeLa-S3',experiment:'ChIP-seq_H3K27ac'},
{name:'wgEncodeUwHistoneHct116H3k4me3StdPkRep1',cell:'HCT116',experiment:'ChIP-seq_H3K4me3'},
{name:'wgEncodeBroadHistoneHsmmH3k9acStdPk',cell:'HSMM',experiment:'ChIP-seq_H3K9ac'},
{name:'wgEncodeUwTfbsMcf7CtcfStdPkRep1',cell:'MCF-7',experiment:'ChIP-seq_CTCF'},
{name:'wgEncodeOpenChromChipHepg2CtcfPk',cell:'HepG2',experiment:'ChIP-seq_CTCF'},
{name:'wgEncodeOpenChromDnaseHepg2Pk',cell:'HepG2',experiment:'DNase-seq'},
{name:'wgEncodeBroadHistoneK562H3k4me1StdPk',cell:'K562',experiment:'ChIP-seq_H3K4me1'},
{name:'wgEncodeBroadHmmHsmmHMM',cell:'HSMM',experiment:'chromHMM'},
{name:'wgEncodeBroadHistoneGm12878H3k4me3StdPk',cell:'GM12878',experiment:'ChIP-seq_H3K4me3'},
{name:'wgEncodeBroadHmmH1hescHMM',cell:'H1-hESC',experiment:'chromHMM'},
{name:'wgEncodeBroadHistoneK562H3k9acStdPk',cell:'K562',experiment:'ChIP-seq_H3K9ac'},
{name:'wgEncodeSydhTfbsHepg2Tcf7l2UcdPk',cell:'HepG2',experiment:'ChIP-seq_TCF7L2'},
{name:'wgEncodeBroadHmmHmecHMM',cell:'HMEC',experiment:'chromHMM'},
{name:'wgEncodeAwgTfbsHaibGm12878Tcf3Pcr1xUniPk',cell:'GM12878',experiment:'ChIP-seq_TCF3'},
{name:'wgEncodeBroadHistoneHmecH3k27acStdPk',cell:'HMEC',experiment:'ChIP-seq_H3K27ac'},
{name:'wgEncodeBroadHistoneGm12878H3k27acStdPk',cell:'GM12878',experiment:'ChIP-seq_H3K27ac'},
{name:'wgEncodeBroadHistoneNhlfH3k09me3Pk',cell:'NHLF',experiment:'ChIP-seq_H3K9me3'},
{name:'wgEncodeBroadHistoneNhlfCtcfStdPk',cell:'NHLF',experiment:'ChIP-seq_CTCF'},
{name:'wgEncodeBroadHistoneA549H3k09acEtoh02Pk',cell:'A549',experiment:'ChIP-seq_H3K9ac'},
{name:'wgEncodeOpenChromFaireHuvecPk',cell:'HUVEC',experiment:'FAIRE-seq'},
{name:'wgEncodeBroadHistoneA549H3k27me3Etoh02Pk',cell:'A549',experiment:'ChIP-seq_H3K27me3'},
{name:'wgEncodeBroadHistoneA549H3k09me3Etoh02Pk',cell:'A549',experiment:'ChIP-seq_H3K9me3'},
{name:'wgEncodeBroadHistoneHuvecH3k9acStdPk',cell:'HUVEC',experiment:'ChIP-seq_H3K9ac'},
{name:'wgEncodeUwTfbsK562CtcfStdPkRep1',cell:'K562',experiment:'ChIP-seq_CTCF'},
{name:'wgEncodeBroadHistoneHuvecH3k27acStdPk',cell:'HUVEC',experiment:'ChIP-seq_H3K27ac'},
{name:'wgEncodeUwHistoneCaco2H3k36me3StdPkRep1',cell:'Caco-2',experiment:'ChIP-seq_H3K36me3'},
{name:'wgEncodeBroadHistoneHepg2H3k09me3Pk',cell:'HepG2',experiment:'ChIP-seq_H3K9me3'},
{name:'wgEncodeBroadHistoneHepg2H3k79me2StdPk',cell:'HepG2',experiment:'ChIP-seq_H3K79me2'},
{name:'wgEncodeBroadHistoneHelas3H3k04me1StdPk',cell:'HeLa-S3',experiment:'ChIP-seq_H3K4me1'},
{name:'wgEncodeBroadHistoneHepg2H3k4me3StdPk',cell:'HepG2',experiment:'ChIP-seq_H3K4me3'},
{name:'wgEncodeOpenChromFaireH1hescPk',cell:'H1-hESC',experiment:'FAIRE-seq'},
{name:'wgEncodeBroadHistoneHepg2H3k36me3StdPk',cell:'HepG2',experiment:'ChIP-seq_H3K36me3'},
{name:'wgEncodeBroadHistoneGm12878H3k4me1StdPk',cell:'GM12878',experiment:'ChIP-seq_H3K4me1'},
{name:'wgEncodeBroadHistoneNhlfH3k36me3StdPk',cell:'NHLF',experiment:'ChIP-seq_H3K36me3'},
{name:'wgEncodeSydhHistoneMcf7H3k27acUcdPk',cell:'MCF-7',experiment:'ChIP-seq_H3K27ac'},
{name:'wgEncodeBroadHistoneH1hescH3k4me3StdPk',cell:'H1-hESC',experiment:'ChIP-seq_H3K4me3'},
{name:'wgEncodeBroadHmmNhlfHMM',cell:'NHLF',experiment:'chromHMM'},
{name:'wgEncodeBroadHmmNhekHMM',cell:'NHEK',experiment:'chromHMM'},
{name:'wgEncodeSydhHistoneHct116H3k04me1UcdPk',cell:'HCT116',experiment:'ChIP-seq_H3K4me1'},
{name:'wgEncodeAwgTfbsBroadHsmmCtcfUniPk',cell:'HSMM',experiment:'ChIP-seq_CTCF'},
{name:'wgEncodeBroadHistoneHuvecH3k36me3StdPk',cell:'HUVEC',experiment:'ChIP-seq_H3K36me3'},
{name:'wgEncodeBroadHmmK562HMM',cell:'K562',experiment:'chromHMM'},
{name:'wgEncodeBroadHistoneHmecH3k36me3StdPk',cell:'HMEC',experiment:'ChIP-seq_H3K36me3'},
{name:'wgEncodeOpenChromDnaseH1hescPk',cell:'H1-hESC',experiment:'DNase-seq'},
{name:'wgEncodeRegTfbsClusteredV3',cell:'None',experiment:'TFBS Region'},
{name:'wgEncodeOpenChromFaireGm12878Pk',cell:'GM12878',experiment:'FAIRE-seq'},
{name:'wgEncodeHaibTfbsHct116CtcfcV0422111PkRep1',cell:'HCT116',experiment:'ChIP-seq_CTCF'},
{name:'wgEncodeSydhTfbsHct116Tcf7l2UcdPk',cell:'HCT116',experiment:'ChIP-seq_TCF7L2'},
{name:'wgEncodeAwgTfbsUwHelas3CtcfUniPk',cell:'HeLa-S3',experiment:'ChIP-seq_CTCF'},
{name:'wgEncodeBroadHistoneGm12878H3k9acStdPk',cell:'GM12878',experiment:'ChIP-seq_H3K9ac'},
{name:'wgEncodeBroadHistoneK562H3k79me2StdPk',cell:'K562',experiment:'ChIP-seq_H3K79me2'},
{name:'wgEncodeBroadHistoneGm12878H3k9me3StdPk',cell:'GM12878',experiment:'ChIP-seq_H3K9me3'},
{name:'wgEncodeUwDnaseNhlfPkRep1',cell:'NHLF',experiment:'DNase-seq'},
{name:'wgEncodeBroadHistoneNhlfH3k27acStdPk',cell:'NHLF',experiment:'ChIP-seq_H3K27ac'},
{name:'wgEncodeBroadHistoneHepg2H3k9acStdPk',cell:'HepG2',experiment:'ChIP-seq_H3K9ac'},
{name:'wgEncodeBroadHistoneHelas3H3k4me3StdPk',cell:'HeLa-S3',experiment:'ChIP-seq_H3K4me3'},
{name:'wgEncodeBroadHistoneH1hescH3k79me2StdPk',cell:'H1-hESC',experiment:'ChIP-seq_H3K79me2'},
{name:'wgEncodeBroadHistoneK562H3k36me3StdPk',cell:'K562',experiment:'ChIP-seq_H3K36me3'},
{name:'wgEncodeBroadHistoneHmecH3k9acStdPk',cell:'HMEC',experiment:'ChIP-seq_H3K9ac'},
{name:'wgEncodeOpenChromChipHuvecCtcfPk',cell:'HUVEC',experiment:'ChIP-seq_CTCF'},
{name:'wgEncodeBroadHistoneHuvecH3k09me3Pk',cell:'HUVEC',experiment:'ChIP-seq_H3K9me3'},
{name:'wgEncodeBroadHistoneH1hescH3k27acStdPk',cell:'H1-hESC',experiment:'ChIP-seq_H3K27ac'},
{name:'wgEncodeBroadHistoneHelas3H3k09me3Pk',cell:'HeLa-S3',experiment:'ChIP-seq_H3K9me3'},
{name:'wgEncodeBroadHistoneNhekH3k4me1StdPk',cell:'NHEK',experiment:'ChIP-seq_H3K4me1'},
{name:'wgEncodeOpenChromDnaseGm12878Pk',cell:'GM12878',experiment:'DNase-seq'},
{name:'wgEncodeHaibMethylRrbsGm12878HaibSitesRep1',cell:'GM12878',experiment:'methyl RRBS'},
{name:'wgEncodeBroadHistoneA549H3k79me2Etoh02Pk',cell:'A549',experiment:'ChIP-seq_H3K79me2'},
{name:'wgEncodeBroadHistoneH1hescH3k4me1StdPk',cell:'H1-hESC',experiment:'ChIP-seq_H3K4me1'},
{name:'wgEncodeBroadHistoneHepg2H3k27acStdPk',cell:'HepG2',experiment:'ChIP-seq_H3K27ac'},
{name:'wgEncodeBroadHistoneHelas3H3k9acStdPk',cell:'HeLa-S3',experiment:'ChIP-seq_H3K9ac'},
{name:'wgEncodeHaibMethylRrbsHct116StanfordSitesRep1',cell:'HCT116',experiment:'methyl RRBS'},
{name:'wgEncodeOpenChromFaireNhekPk',cell:'NHEK',experiment:'FAIRE-seq'},
{name:'wgEncodeSydhHistoneHct116H3k27acUcdPk',cell:'HCT116',experiment:'ChIP-seq_H3K27ac'},
{name:'wgEncodeBroadHistoneHepg2H3k27me3StdPk',cell:'HepG2',experiment:'ChIP-seq_H3K27me3'},
{name:'wgEncodeUwDnaseNhekPkRep1',cell:'NHEK',experiment:'DNase-seq'},
{name:'wgEncodeOpenChromFaireA549Pk',cell:'A549',experiment:'FAIRE-seq'},
{name:'wgEncodeBroadHistoneH1hescH3k09me3StdPk',cell:'H1-hESC',experiment:'ChIP-seq_H3K9me3'},
{name:'wgEncodeHaibMethylRrbsCaco2UwSitesRep1',cell:'Caco-2',experiment:'methyl RRBS'},
{name:'wgEncodeBroadHistoneHsmmH3k79me2StdPk',cell:'HSMM',experiment:'ChIP-seq_H3K79me2'},
{name:'wgEncodeBroadHistoneHsmmH3k4me3StdPk',cell:'HSMM',experiment:'ChIP-seq_H3K4me3'},
{name:'wgEncodeUwTfbsA549CtcfStdPkRep1',cell:'A549',experiment:'ChIP-seq_CTCF'},
{name:'wgEncodeUwHistoneCaco2H3k4me3StdPkRep1',cell:'Caco-2',experiment:'ChIP-seq_H3K4me3'},
{name:'wgEncodeOpenChromDnaseHuvecPk',cell:'HUVEC',experiment:'DNase-seq'},
{name:'wgEncodeBroadHistoneGm12878H3k27me3StdPk',cell:'GM12878',experiment:'ChIP-seq_H3K27me3'},
{name:'wgEncodeAwgTfbsBroadNhekCtcfUniPk',cell:'NHEK',experiment:'ChIP-seq_CTCF'},
{name:'wgEncodeUwDnaseK562PkRep1',cell:'K562',experiment:'DNase-seq'},
{name:'wgEncodeBroadHistoneHmecH3k79me2Pk',cell:'HMEC',experiment:'ChIP-seq_H3K79me2'},
{name:'wgEncodeHaibMethylRrbsK562HaibSitesRep1',cell:'K562',experiment:'methyl RRBS'},
{name:'wgEncodeBroadHistoneHmecH3k4me3StdPk',cell:'HMEC',experiment:'ChIP-seq_H3K4me3'},
{name:'wgEncodeUwDnaseHsmmPkRep1',cell:'HSMM',experiment:'DNase-seq'},
{name:'wgEncodeBroadHistoneK562H3k27acStdPk',cell:'K562',experiment:'ChIP-seq_H3K27ac'},
{name:'wgEncodeUwHistoneCaco2H3k27me3StdPkRep1',cell:'Caco-2',experiment:'ChIP-seq_H3K27me3'},
{name:'wgEncodeUwDnaseMcf7PkRep1',cell:'MCF-7',experiment:'DNase-seq'},
{name:'wgEncodeUwHistoneMcf7H3k4me3StdPkRep1',cell:'MCF-7',experiment:'ChIP-seq_H3K4me3'},
{name:'wgEncodeBroadHistoneHmecH3k09me3Pk',cell:'HMEC',experiment:'ChIP-seq_H3K9me3'},
{name:'wgEncodeBroadHistoneK562H3k9me3StdPk',cell:'K562',experiment:'ChIP-seq_H3K9me3'},
{name:'wgEncodeOpenChromFaireHepg2Pk',cell:'HepG2',experiment:'FAIRE-seq'},
{name:'wgEncodeBroadHistoneHuvecH3k4me3StdPk',cell:'HUVEC',experiment:'ChIP-seq_H3K4me3'},
{name:'wgEncodeBroadHistoneNhekH3k79me2Pk',cell:'NHEK',experiment:'ChIP-seq_H3K79me2'},
{name:'wgEncodeBroadHistoneHelas3H3k79me2StdPk',cell:'HeLa-S3',experiment:'ChIP-seq_H3K79me2'},
{name:'wgEncodeBroadHistoneNhekH3k36me3StdPk',cell:'NHEK',experiment:'ChIP-seq_H3K36me3'},
{name:'wgEncodeBroadHistoneNhekH3k27acStdPk',cell:'NHEK',experiment:'ChIP-seq_H3K27ac'},
{name:'wgEncodeAwgTfbsBroadGm12878CtcfUniPk',cell:'GM12878',experiment:'ChIP-seq_CTCF'},
{name:'wgEncodeUwDnaseHelas3PkRep1',cell:'HeLa-S3',experiment:'DNase-seq'},
{name:'wgEncodeOpenChromChipH1hescCtcfPk',cell:'H1-hESC',experiment:'ChIP-seq_CTCF'},
{name:'wgEncodeBroadHistoneHelas3H3k27me3StdPk',cell:'HeLa-S3',experiment:'ChIP-seq_H3K27me3'},
{name:'wgEncodeBroadHistoneHsmmH3k9me3StdPk',cell:'HSMM',experiment:'ChIP-seq_H3K9me3'},
{name:'wgEncodeBroadHistoneA549H3k36me3Etoh02Pk',cell:'A549',experiment:'ChIP-seq_H3K36me3'},
{name:'wgEncodeBroadHistoneNhekH3k09me3Pk',cell:'NHEK',experiment:'ChIP-seq_H3K9me3'},
{name:'tfbsConsSites',cell:'None',experiment:'TFBS Conservation'},
{name:'wgEncodeBroadHistoneK562H3k27me3StdPk',cell:'K562',experiment:'ChIP-seq_H3K27me3'},
{name:'wgEncodeHaibMethylRrbsHelas3HaibSitesRep1',cell:'HeLa-S3',experiment:'methyl RRBS'},
{name:'wgEncodeHaibMethylRrbsMcf7DukeSitesRep1',cell:'MCF-7',experiment:'methyl RRBS'},
{name:'wgEncodeSydhHistoneMcf7H3k36me3bUcdPk',cell:'MCF-7',experiment:'ChIP-seq_H3K36me3'},
{name:'wgEncodeBroadHistoneNhekH3k4me3StdPk',cell:'NHEK',experiment:'ChIP-seq_H3K4me3'},
{name:'wgEncodeBroadHistoneHelas3H3k36me3StdPk',cell:'HeLa-S3',experiment:'ChIP-seq_H3K36me3'},
{name:'wgEncodeBroadHistoneGm12878H3k79me2StdPk',cell:'GM12878',experiment:'ChIP-seq_H3K79me2'},
{name:'wgEncodeOpenChromFaireHelas3Pk',cell:'HeLa-S3',experiment:'FAIRE-seq'},
{name:'wgEncodeUwDnaseCaco2PkRep1',cell:'Caco-2',experiment:'DNase-seq'},
{name:'wgEncodeBroadHistoneHmecH3k4me1StdPk',cell:'HMEC',experiment:'ChIP-seq_H3K4me1'},
{name:'wgEncodeUwDnaseHct116PkRep1',cell:'HCT116',experiment:'DNase-seq'},
{name:'wgEncodeBroadHistoneNhlfH3k4me1StdPk',cell:'NHLF',experiment:'ChIP-seq_H3K4me1'},
{name:'wgEncodeBroadHistoneA549H3k27acEtoh02Pk',cell:'A549',experiment:'ChIP-seq_H3K27ac'},
{name:'wgEncodeBroadHistoneA549H3k04me1Etoh02Pk',cell:'A549',experiment:'ChIP-seq_H3K4me1'},
{name:'wgEncodeHaibMethylRrbsA549Dm002p7dHaibSitesRep1',cell:'A549',experiment:'methyl RRBS'},
{name:'wgEncodeBroadHistoneHepg2H3k04me1StdPk',cell:'HepG2',experiment:'ChIP-seq_H3K4me1'},
{name:'wgEncodeUwDnaseHmecPkRep1',cell:'HMEC',experiment:'DNase-seq'},
{name:'wgEncodeAwgTfbsBroadHmecCtcfUniPk',cell:'HMEC',experiment:'ChIP-seq_CTCF'},
{name:'wgEncodeBroadHistoneHuvecH3k27me3StdPk',cell:'HUVEC',experiment:'ChIP-seq_H3K27me3'} ];

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
	if (i>19)
	{
	    alert('At most 20 tracks can be selected.');
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
    for (var i=0;i<20-tracks.length;i++)
    {
	var newrow=document.createElement('tr');
	var col=document.createElement('td');
	var label=document.createElement('label');
	var upload=document.createElement('input');
	label.innerHTML='Custom track (BED format;.gz okay)';
	upload.type='file';
	upload.name='custom_table';

	label.appendChild(upload);
	col.appendChild(label);
	newrow.appendChild(col);
	insertPos.appendChild(newrow);
    }
}

function response_to_select_region()
{
alert("response_to_select_region() called");
alert($(this).val());
    var region_spec_container=$("td.region_detail_area");
    if($(this).val()=='snp')
    {
    	region_spec_container.html("<table><tr>		<td>Index SNP</td>		<td><input type='text' name='refsnp' size=15 /></td>		</tr>		<tr>		<td>Flanking region (kb)</td>		<td><input type='text' name='snpflank' size=15 value='200'/></td>		</tr></table>");
    }
    else if ($(this).val()=='gene')
    {
    	region_spec_container.html("<table>                <tr>		<td>Reference Gene</td>		<td><input type='text' name='refgene' size=15 /></td>		</tr>		<tr>		<td>Flanking region (kb)</td>		<td><input type='text' name='geneflank' size=15 value='200' /></td>		<tr>		<td>Optional Index SNP (default is SNP with lowest P value)</td>		<td><input type='text' name='refsnp_for_gene' size=15 /></td>		</tr></table>");
    }
    else if($(this).val()=='chr')
    {
    	region_spec_container.html("<table>		<tr>		<td>Chromosome</td>		<td><select name='chr' ><option value='1'>1</option><option value='2'>2</option><option value='3'>3</option><option value='4'>4</option><option value='5'>5</option><option value='6'>6</option><option value='7'>7</option><option value='8'>8</option><option value='9'>9</option><option value='10'>10</option><option value='11'>11</option><option value='12'>12</option><option value='13'>13</option><option value='14'>14</option><option value='15'>15</option><option value='16'>16</option><option value='17'>17</option><option value='18'>18</option><option value='19'>19</option><option value='20'>20</option><option value='21'>21</option><option value='22'>22</option><option value='X'>X</option></select></td>		</tr>		<tr>		<td>Start (Mb)</td>		<td><input type='text' name='start' size=15 /></td>		<tr>		<td>End (Mb)</td>		<td><input type='text' name='end' size=15 /></td>		<tr>		<td>Optional Index SNP (default is SNP with lowest P value)</td>		<td><input type='text' name='refsnp_for_chr' size=15 /></td>		</tr></table>");
    }
}

function response_to_multi_select_region()
{
    var region_spec_container=$("td.multi_region_detail_area");

    if($(this).value=='region_file')
    {
    	region_spec_container.html("<table>		<tr>		<td>Choose a region specification file</td>		<td><input type='file' name='region_file' size=15 /></td>		</tr>		<tr>		<td>HitSpec format is supported, BUT 7th column and beyond are IGNORED</td>		</tr>		<tr>		<td><a href='http://genome.sph.umich.edu/wiki/LocusZoom#Generating_a_Hit_Spec_File'>Help with HitSpec</a></td>		</tr></table>");
    }
    else if($(this).value=='multi_region')
    {
    	region_spec_container.html("<tr><td><table border=1 class='single_region_spec_head'><tr>	<td class='region_method_area'>	    <input type='radio' name='region_method' onclick='response_to_select_region()' value='snp' checked >Reference SNP<br>	     <input type='radio' name='region_method' onclick='response_to_select_region()' value='gene'>Reference Gene<br>	     <input type='radio' name='region_method' onclick='response_to_select_region()' value='chr'>Chromosomal Region<br>	    </td></tr><tr><td class='region_detail_area'> </td></tr></td><td><table border=1 class='single_region_spec_head'><tr>	<td class='region_method_area'>	    <input type='radio' name='region_method' onclick='response_to_select_region()' value='snp' checked >Reference SNP<br>	     <input type='radio' name='region_method' onclick='response_to_select_region()' value='gene'>Reference Gene<br>	     <input type='radio' name='region_method' onclick='response_to_select_region()' value='chr'>Chromosomal Region<br>	    </td></tr><tr><td class='region_detail_area'> </td></tr></td><td><table border=1 class='single_region_spec_head'><tr>	<td class='region_method_area'>	    <input type='radio' name='region_method' onclick='response_to_select_region()' value='snp' checked >Reference SNP<br>	     <input type='radio' name='region_method' onclick='response_to_select_region()' value='gene'>Reference Gene<br>	     <input type='radio' name='region_method' onclick='response_to_select_region()' value='chr'>Chromosomal Region<br>	    </td></tr><tr><td class='region_detail_area'> </td></tr></td></tr><tr><td><table border=1 class='single_region_spec_head'><tr>	<td class='region_method_area'>	    <input type='radio' name='region_method' onclick='response_to_select_region()' value='snp' checked >Reference SNP<br>	     <input type='radio' name='region_method' onclick='response_to_select_region()' value='gene'>Reference Gene<br>	     <input type='radio' name='region_method' onclick='response_to_select_region()' value='chr'>Chromosomal Region<br>	    </td></tr><tr><td class='region_detail_area'> </td></tr></td><td><table border=1 class='single_region_spec_head'><tr>	<td class='region_method_area'>	    <input type='radio' name='region_method' onclick='response_to_select_region()' value='snp' checked >Reference SNP<br>	     <input type='radio' name='region_method' onclick='response_to_select_region()' value='gene'>Reference Gene<br>	     <input type='radio' name='region_method' onclick='response_to_select_region()' value='chr'>Chromosomal Region<br>	    </td></tr><tr><td class='region_detail_area'> </td></tr></td><td><table border=1 class='single_region_spec_head'><tr>	<td class='region_method_area'>	    <input type='radio' name='region_method' onclick='response_to_select_region()' value='snp' checked >Reference SNP<br>	     <input type='radio' name='region_method' onclick='response_to_select_region()' value='gene'>Reference Gene<br>	     <input type='radio' name='region_method' onclick='response_to_select_region()' value='chr'>Chromosomal Region<br>	    </td></tr><tr><td class='region_detail_area'> </td></tr></td></tr><tr><td><table border=1 class='single_region_spec_head'><tr>	<td class='region_method_area'>	    <input type='radio' name='region_method' onclick='response_to_select_region()' value='snp' checked >Reference SNP<br>	     <input type='radio' name='region_method' onclick='response_to_select_region()' value='gene'>Reference Gene<br>	     <input type='radio' name='region_method' onclick='response_to_select_region()' value='chr'>Chromosomal Region<br>	    </td></tr><tr><td class='region_detail_area'> </td></tr></td><td><table border=1 class='single_region_spec_head'><tr>	<td class='region_method_area'>	    <input type='radio' name='region_method' onclick='response_to_select_region()' value='snp' checked >Reference SNP<br>	     <input type='radio' name='region_method' onclick='response_to_select_region()' value='gene'>Reference Gene<br>	     <input type='radio' name='region_method' onclick='response_to_select_region()' value='chr'>Chromosomal Region<br>	    </td></tr><tr><td class='region_detail_area'> </td></tr></td><td><table border=1 class='single_region_spec_head'><tr>	<td class='region_method_area'>	    <input type='radio' name='region_method' onclick='response_to_select_region()' value='snp' checked >Reference SNP<br>	     <input type='radio' name='region_method' onclick='response_to_select_region()' value='gene'>Reference Gene<br>	     <input type='radio' name='region_method' onclick='response_to_select_region()' value='chr'>Chromosomal Region<br>	    </td></tr><tr><td class='region_detail_area'> </td></tr></td></tr>");
	$(region_spec_container).find("table.single_region_spec_head").each(
		function()
		{
		  $(this).find("td.region_method_area input").first().trigger("click");
		}
	);
    }
}

function toggle_single_multi_region()
{
alert(374);
    var caller=$("#region_multi_single_button_id");
    var container=$("#region_specification_div_id");
    alert($(container).val());
    if($(caller).val()=='single')
    {
alert(268);
        $(caller).val('multi');
        container.html("<table border=1 class='single_region_spec_head'><tr>	<td class='region_method_area'>	    <input type='radio' name='region_method' onclick='response_to_select_region()' value='snp' checked >Reference SNP<br>	     <input type='radio' name='region_method' onclick='response_to_select_region()' value='gene'>Reference Gene<br>	     <input type='radio' name='region_method' onclick='response_to_select_region()' value='chr'>Chromosomal Region<br>	    </td></tr><tr><td class='region_detail_area'> </td></tr>");
	var i=container.find("td.region_method_area input").first();
	i.ready(response_to_select_region());
    }
    else if ($(caller).val()=='multi')
    {
alert(275);
        $(caller).val('single');
        container.html("<table border=1><tr><td class=multi_region_method_area'><input type='radio' name='multi_region_method' onclick='response_to_multi_select_region()' value='multi_region'>Manually Specify multi-region<br><input type='radio' name='multi_region_method' onclick='response_to_multi_select_region()' value='region_file'>Region Spefication File<br><tr><td class='multi_region_detail_area'> </td></tr>");
	container.find("td.multi_region_method_area input").first().click(response_to_multi_select_region());
    }
    alert($(caller).val());
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

    $("#region_multi_single_button_id").val("single");
    $("#region_multi_single_button_id").trigger("click");

    $("td.region_detail_area input[name='snpflank']").val("50");
    $("td.region_detail_area input[name='refsnp']").val("rs10318");

    document.getElementById('generic_toggle_id').checked=true;
    document.getElementById('anno_toggle_id').checked=true;
    document.getElementById('avinput_id').checked=false;
    document.getElementById('ref_hg19').checked=true;

    //set advanced options
    document.getElementById('ld_toggle_id').checked=true;

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
    if (email)
    {
    	var email_pattern=/[\w\-\.]+\@[\w\-\.]+\.[\w\-\.]+/;

    	if (! email_pattern.test(email))
    	{
    	    alert('Illegal email address!');
    	    return false;
    	}
    } else
    {
    //when multiple regions are specified, the job will take a while
    //user should provide email
        if($("#region_multi_single_button_id").value=='single')
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
    var col_pat=/[^\w\-]/;

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
	    alert ("No annotation data tracks selected or uploaded \nwhile generic plot or annotation is enabled.");
	    return false;
	}
    }
    if ( datatrack.length+custom_table.length>20)
    {
	alert('Too many data tracks (max: 20)');
	return false;
    }


    //region specification
    var region_pat=/[ \$\t\r\n\*\|\?\>\<\'\"\,\;\:\[\]\{\}]/;
    var region_method=document.getElementsByName('region_method');

    
    //user must either upload a region specification file
    //or specify region for each region specification table

    if(! $("input[name='region_file']").val() )
    {
    $(region_method).each(
     function() {
        var refsnp=$("table.single_region_spec_head").find("input[name='refsnp']").val();
        var snpflank=$("table.single_region_spec_head").find("input[name='snpflank']").val();
        var refgene=$("table.single_region_spec_head").find("input[name='refgene']").val();
        var geneflank=$("table.single_region_spec_head").find("input[name='geneflank']").val();
        var generefsnp=$("table.single_region_spec_head").find("input[name='refsnp_for_gene']").val();
        var chr=$("table.single_region_spec_head").find("input[name='chr']").val();
        var start=$("table.single_region_spec_head").find("input[name='start']").val();
        var end=$("table.single_region_spec_head").find("input[name='end']").val();
        var chrrefsnp=$("table.single_region_spec_head").find("input[name='refsnp_for_chr']").val();

        if ($(this).value == 'snp')
        {
        	if ( refsnp.length==0 || snpflank.length==0)
        	{
        		alert('No reference SNP or flanking region');
        		return false;
        	} else if (region_pat.test(refsnp) || region_pat.test(snpflank))
        	{
        		alert("Illegal characters found in reference SNP or flanking regin\nPlease remove $ ' \" { } [ ] \\ > < : ; , * | and tab, space, newline.");
        		return false;
        	}	
        } else if ($(this).value == 'gene')
        {
        	if ( refgene.length==0 || geneflank.length==0)
            {
            	alert('No reference gene or flanking region');
            	return false;
            } else if (region_pat.test(refgene) || region_pat.test(geneflank) || region_pat.test(generefsnp))
            {
            	alert("Illegal characters found in reference SNP or flanking regin\nPlease remove $ ' \" { } [ ] \\ > < : ; , * | and tab, space, newline.");
            	return false;
            }	
        } else if ($(this).value == 'chr')
        {
        	if ( chr.length==0 || start.length==0 || end.length==0)
        	{
        		alert('No chromosome name or start or end');
        		return false;
        	} else if (region_pat.test(chr) || region_pat.test(start) || region_pat.test(end) || region_pat.test(chrrefsnp))
        	{
        		alert("Illegal characters found in reference SNP or flanking regin\nPlease remove $ ' \" { } [ ] \\ > < : ; , * | and tab, space, newline.");
        		return false;
        	}	
        }
     }
    );
    }
}

//]]></script>
<noscript>
	<h1>
		Your browser does not support JavaScript! </br>Please enable JavaScript to use Enlight.
	</h1>
</noscript>
<h2>
	Introduction
</h2>
<p>
	Enlight draws regional plots for GWAS results, and overlays epigenetic modification, DNase sensitivity site, transcription factor binding annotation onto it. The combined plot will help identify causal variants. Users can also upload custom annotation, obtain text annotation for each SNP.<br><br>
</p>
<form method="post" action="/cgi-bin/process.cgi" enctype="multipart/form-data" name="main" onsubmit="return check_before_submission();"><h2>
	Input
</h2>
<table border="0">
	<tr>
		<td>DEMO<br>
			        <a href='/example/rs10318.txt'>(example input)</a><br>
				<a href='/example/rs10318_out/index.html'>(example output)</a></td> <td><button type='button' onclick='loadExampleSetting()'>Load settings for example input</button>
	    <br>
	    <button type='button' onclick='loadExampleInput()'>Load example input</button></td>
	</tr>
	<tr>
		<td><span title='receive result link'>Email (mandatory for multi-region)</span></td> <td><input name='email' id='email_id' type='email' onclick="this.value=''" /></td>
	</tr>
	<tr>
		<td>Input file (1st line is header; .gz okay)</td> <td id="query_cell_id"><input type="file" name="query"  id="query_file_id" /> </br></br>or paste URL <input name='query_URL' type='url' id='query_URL_id' /></td>
	</tr>
	<tr>
		<td>Field delimiter</td> <td><label>
	 <input type="radio" name="qformat" value="whitespace" checked="checked" id="qformat_whitespace" />whitespace
</label> <label>
	 <input type="radio" name="qformat" value="tab" id="qformat_whitespace" />tab
</label> <label>
	 <input type="radio" name="qformat" value="space" id="qformat_whitespace" />space
</label> <label>
	 <input type="radio" name="qformat" value="comma" id="qformat_whitespace" />comma
</label></td>
	</tr>
	<tr>
		<td><span title='this columns contains rsID'>Marker Column (case sensitive)</span></td> <td><input type="text" name="markercol"  id="markercol_id" onclick="this.value=''" /></td>
	</tr>
	<tr>
		<td>P value column (case-sensitive)</td> <td><input type="text" name="pvalcol"  onclick="this.value=''" id="pvalcol_id" /></td>
	</tr>
	<tr>
		<td>Genome Build</td><td><label>
		<input type="radio" name="ref" value="hg18">hg18
		</label>
		<label>
		<input type="radio" name="ref" id="ref_hg19" value="hg19" checked="checked">hg19
		</label></td>
	</tr>
	<tr>
		<td><span title='choose data set for computing Linkage Disequilibrium'>Genome Build/LD source/Population</span></td> <td><select name="source_ref_pop"  id="source_ref_pop_id">
<option value="1000G_Aug2009,hg18,CEU">1000G_Aug2009,hg18,CEU</option>
<option value="1000G_Aug2009,hg18,JPT+CHB">1000G_Aug2009,hg18,JPT+CHB</option>
<option value="1000G_Aug2009,hg18,YRI">1000G_Aug2009,hg18,YRI</option>
<option value="1000G_June2010,hg18,CEU">1000G_June2010,hg18,CEU</option>
<option value="1000G_June2010,hg18,JPT+CHB">1000G_June2010,hg18,JPT+CHB</option>
<option value="1000G_June2010,hg18,YRI">1000G_June2010,hg18,YRI</option>
<option value="1000G_March2012,hg19,AFR">1000G_March2012,hg19,AFR</option>
<option value="1000G_March2012,hg19,AMR">1000G_March2012,hg19,AMR</option>
<option value="1000G_March2012,hg19,ASN">1000G_March2012,hg19,ASN</option>
<option selected="selected" value="1000G_March2012,hg19,EUR">1000G_March2012,hg19,EUR</option>
<option value="1000G_Nov2010,hg19,AFR">1000G_Nov2010,hg19,AFR</option>
<option value="1000G_Nov2010,hg19,ASN">1000G_Nov2010,hg19,ASN</option>
<option value="1000G_Nov2010,hg19,EUR">1000G_Nov2010,hg19,EUR</option>
<option value="hapmap,hg18,CEU">hapmap,hg18,CEU</option>
<option value="hapmap,hg18,JPT+CHB">hapmap,hg18,JPT+CHB</option>
<option value="hapmap,hg18,YRI">hapmap,hg18,YRI</option>
</select></td>
	</tr>
	<tr>
		<td><span title='show if a variant appears in a particular database'>Mark variants in database: </span></td> <td><select name="varAnno"  id="varAnno_id">
<option value="GTEx_eQTL_11162013">GTEx_eQTL_11162013</option>
<option value="GWAS_CAT_11242013">GWAS_CAT_11242013</option>
<option value="UChgo_eQTL_11162013">UChgo_eQTL_11162013</option>
<option selected="selected" value="NULL">NULL</option>
</select></td>
	</tr>
</table>
<br> <br>
<h2>
	<span title='plot region'>Specify a region</span>
</h2>
<div>
	<table class="noborder">
		<tr>
			<td><p><button type='button' value='single' id='region_multi_single_button_id' onlick='toggle_single_multi_region();'>Toggle to Select Single or Multiple Regions</button></p></td>
		</tr>
		<tr>
			<td><div id='region_specification_div_id'></div></td>
		</tr>
	</table>
</div>
<br> <br>
<h2>
	<span title='Plot HiC interaction heatmap'>HiC interaction plot</span>
</h2>
<table class="noborder">
	<tr>
		<td colspan="2"><span title='Do you want an HiC interaction heatmap plot?'><label>
	 <input type="checkbox" name="heatmap_toggle" value="on" checked="checked" id="heatmap_toggle_id" />Output interaction heatmap?
</label>
</span></td>
	</tr>
	<tr>
		<td>Interaction type (resolution)</td><td><label>
		<input type="radio" name="interaction_type" value="interchromosomal" >INTERchromosomal(1Mb)
		</label>
		<input type="radio" name="interaction_type" value="intrachromosomal" checked="checked">INTRAchromosomal(100Kb)
		</label></td>
	</tr>
	<tr>
		<td>Cell lines</td><td><label>
		<input type="radio" name="interaction_cell_type" value="k562" >K562
		</label>
		<input type="radio" name="interaction_cell_type" value="gm06690" checked="checked">GM06690
		</label></td>
	</tr>
</table>
<br> <br>
<h2>
	<span title='show signal strengths in regions'>Generic plot (using UCSC BED tables)</span>
</h2>
<table class="noborder">
	<tr>
		<td colspan="2"><span title='Do you want a generic (annotation) plot?'><label>
	 <input type="checkbox" name="generic_toggle" value="on" checked="checked" id="generic_toggle_id" />Generic plot?
</label>
</span></td>
	</tr>
	<tr>
		<td colspan="2"><span title='Do you want text annotation?'><label>
	 <input type="checkbox" name="anno_toggle" value="on" id="anno_toggle_id" />Output ANNOVAR annotation?
</label>
</span></td>
	</tr>
	<tr>
		<td colspan="2"><span title='First 5 columns correspond to chromosome,start,end,alternative allele,reference allele'><label>
	 <input type="checkbox" name="avinput" value="on" id="avinput_id" />Input file in ANNOVAR format?
</label>
</span></td>
	</tr>
	<tr>
		<td>Advanced options</td><td><label>
		<input type="radio" name="detail_toggle" value="show" onclick="showDetail()">show
		</label>
		<input type="radio" name="detail_toggle" value="hide" onclick="hideDetail()" checked="checked">hide
		</label></td>
	</tr>
</table>
<table class="advanced" id="option_detail_id" style="display:none">
	<tr>
		<td><label>
	 <input type="checkbox" name="ld_toggle" value="on" checked="checked" id="ld_toggle_id" />Output linkage disequilibrium information (written in input file)
</label></td>
	</tr>
</table>
</br></br><p class="center">
	<b>Please upload your own files <b style="color:red">AFTER</b> selecting data tracks.</b><br>
</p>
<table>
	<tr>
		<th>
			Cell Line
		</th>
		<th>
			Experiment Type
		</th>
		<th>
			Data Tracks (max: 20; <a class='button' href="/example/example.bed"><strong>BED Example</strong></a>)
		</th>
	</tr>
	<tr>
		<td class="table_align"><table class="noborder left_aln">
			<tr>
				<td><span title='Human lung carcinoma cell line
'><label>
	 <input type="checkbox" name="" value="A549" onchange="changeTracks()" id="A549" class="cell" />A549
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='Human colorectal adenocarcinoma cell line
'><label>
	 <input type="checkbox" name="" value="Caco-2" class="cell" id="Caco-2" onchange="changeTracks()" />Caco-2
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='Human lymphoblastoid cell line
'><label>
	 <input type="checkbox" name="" value="GM12878" onchange="changeTracks()" id="GM12878" class="cell" />GM12878
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='H1 human embryonic stem cells
'><label>
	 <input type="checkbox" name="" value="H1-hESC" id="H1-hESC" class="cell" onchange="changeTracks()" />H1-hESC
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='Human colorectal carcinoma
'><label>
	 <input type="checkbox" name="" value="HCT116" onchange="changeTracks()" id="HCT116" class="cell" />HCT116
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='Human Mammary Epithelial Cells
'><label>
	 <input type="checkbox" name="" value="HMEC" class="cell" id="HMEC" onchange="changeTracks()" />HMEC
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='Human skeletal muscle myoblasts
'><label>
	 <input type="checkbox" name="" value="HSMM" onchange="changeTracks()" class="cell" id="HSMM" />HSMM
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='Human umbilical vein endothelial cell
'><label>
	 <input type="checkbox" name="" value="HUVEC" onchange="changeTracks()" id="HUVEC" class="cell" />HUVEC
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='Human cervical cancer cell line
'><label>
	 <input type="checkbox" name="" value="HeLa-S3" onchange="changeTracks()" id="HeLa-S3" class="cell" />HeLa-S3
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='Human hepatoma cell line
'><label>
	 <input type="checkbox" name="" value="HepG2" onchange="changeTracks()" id="HepG2" class="cell" />HepG2
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='Human chronic myelogenous leukemia cell line
'><label>
	 <input type="checkbox" name="" value="K562" onchange="changeTracks()" class="cell" id="K562" />K562
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='Human breast cancer cell line
'><label>
	 <input type="checkbox" name="" value="MCF-7" onchange="changeTracks()" class="cell" id="MCF-7" />MCF-7
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='Normal Human Epidermal Keratinocytes
'><label>
	 <input type="checkbox" name="" value="NHEK" onchange="changeTracks()" class="cell" id="NHEK" />NHEK
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='Normal Human Lung Fibroblasts
'><label>
	 <input type="checkbox" name="" value="NHLF" onchange="changeTracks()" class="cell" id="NHLF" />NHLF
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='Not a specific cell line
'><label>
	 <input type="checkbox" name="" value="None" id="None" class="cell" onchange="changeTracks()" />None
</label>
</span></td>
			</tr>
		</table></td> <td class="table_align"><table class="noborder left_aln">
			<tr>
				<td><span title='This track reports the enrichment of CTCF binding measured by ChIP-seq. CTCF is a transcription regulator that could bind to insulator sequence.
'><label>
	 <input type="checkbox" name="" value="ChIP-seq_CTCF" onchange="changeTracks()" id="ChIP-seq_CTCF" class="experiment" />ChIP-seq_CTCF
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='This track reports the enrichment of an epigenetic marker measured by ChIP-seq.
'><label>
	 <input type="checkbox" name="" value="ChIP-seq_H3K27ac" class="experiment" id="ChIP-seq_H3K27ac" onchange="changeTracks()" />ChIP-seq_H3K27ac
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='This track reports the enrichment of an epigenetic marker measured by ChIP-seq.
'><label>
	 <input type="checkbox" name="" value="ChIP-seq_H3K27me3" onchange="changeTracks()" class="experiment" id="ChIP-seq_H3K27me3" />ChIP-seq_H3K27me3
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='This track reports the enrichment of an epigenetic marker measured by ChIP-seq.
'><label>
	 <input type="checkbox" name="" value="ChIP-seq_H3K36me3" onchange="changeTracks()" id="ChIP-seq_H3K36me3" class="experiment" />ChIP-seq_H3K36me3
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='This track reports the enrichment of an epigenetic marker measured by ChIP-seq.
'><label>
	 <input type="checkbox" name="" value="ChIP-seq_H3K4me1" onchange="changeTracks()" id="ChIP-seq_H3K4me1" class="experiment" />ChIP-seq_H3K4me1
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='This track reports the enrichment of an epigenetic marker measured by ChIP-seq.
'><label>
	 <input type="checkbox" name="" value="ChIP-seq_H3K4me3" id="ChIP-seq_H3K4me3" class="experiment" onchange="changeTracks()" />ChIP-seq_H3K4me3
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='This track reports the enrichment of an epigenetic marker measured by ChIP-seq.
'><label>
	 <input type="checkbox" name="" value="ChIP-seq_H3K79me2" class="experiment" id="ChIP-seq_H3K79me2" onchange="changeTracks()" />ChIP-seq_H3K79me2
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='This track reports the enrichment of an epigenetic marker measured by ChIP-seq.
'><label>
	 <input type="checkbox" name="" value="ChIP-seq_H3K9ac" onchange="changeTracks()" id="ChIP-seq_H3K9ac" class="experiment" />ChIP-seq_H3K9ac
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='This track reports the enrichment of an epigenetic marker measured by ChIP-seq.
'><label>
	 <input type="checkbox" name="" value="ChIP-seq_H3K9me3" class="experiment" id="ChIP-seq_H3K9me3" onchange="changeTracks()" />ChIP-seq_H3K9me3
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='This track reports the enrichment of TCF3 binding measured by ChIP-seq. TCF3 is a transcription factor.
'><label>
	 <input type="checkbox" name="" value="ChIP-seq_TCF3" onchange="changeTracks()" class="experiment" id="ChIP-seq_TCF3" />ChIP-seq_TCF3
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='This track reports the enrichment of TCF7L2 binding measured by ChIP-seq. TCF7L2 is a transcription factor in Wnt pathway.
'><label>
	 <input type="checkbox" name="" value="ChIP-seq_TCF7L2" onchange="changeTracks()" class="experiment" id="ChIP-seq_TCF7L2" />ChIP-seq_TCF7L2
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='This track reports DNase Hyper-sensitivity Sites measured by DNase-seq.
'><label>
	 <input type="checkbox" name="" value="DNase-seq" id="DNase-seq" class="experiment" onchange="changeTracks()" />DNase-seq
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='This track reports nucleosome-depleted regions of the genome measured by FAIRE-seq.
'><label>
	 <input type="checkbox" name="" value="FAIRE-seq" onchange="changeTracks()" id="FAIRE-seq" class="experiment" />FAIRE-seq
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='This track contains the location and score of transcription factor binding sites conserved in the human/mouse/rat alignment.
'><label>
	 <input type="checkbox" name="" value="TFBS Conservation" onchange="changeTracks()" id="TFBS Conservation" class="experiment" />TFBS Conservation
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='"This track shows regions where transcription factors, proteins responsible for modulating gene transcription, bind to DNA as assayed by ChIP-seq."
'><label>
	 <input type="checkbox" name="" value="TFBS Region" class="experiment" id="TFBS Region" onchange="changeTracks()" />TFBS Region
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='This track displays a chromatin state segmentation for each cell line. The states were computed integrating multiple ChIP-seq data sets using HMM method.
'><label>
	 <input type="checkbox" name="" value="chromHMM" class="experiment" id="chromHMM" onchange="changeTracks()" />chromHMM
</label>
</span></td>
			</tr>
			<tr>
				<td><span title='"The track reports the percentage of DNA molecules that exhibit cytosine methylation at specific CpG dinucleotides. The score in this track reports the number of sequencing reads obtained for each CpG, which is often called 'coverage'. The score is capped at 1000, so any CpGs that were covered by more than 1000 sequencing reads have a score of 1000."
'><label>
	 <input type="checkbox" name="" value="methyl RRBS" class="experiment" id="methyl RRBS" onchange="changeTracks()" />methyl RRBS
</label>
</span></td>
			</tr>
		</table></td> <td class="table_align"><table class="noborder left_aln" id="dataTrackHere">
	<p>
		
	</p>
</table></td>
	</tr>
</table>
<table class="noborder">
	<tr>
		<td><p>
	<input type="submit" name="Submit" value="Submit" /> <input type="reset"  name=".reset" />
</p></td>
	</tr>
</table>
<div><input type="hidden" name=".cgifields" value="anno_toggle"  /><input type="hidden" name=".cgifields" value="qformat"  /><input type="hidden" name=".cgifields" value="ld_toggle"  /><input type="hidden" name=".cgifields" value="avinput"  /><input type="hidden" name=".cgifields" value="generic_toggle"  /><input type="hidden" name=".cgifields" value=""  /><input type="hidden" name=".cgifields" value="heatmap_toggle"  /></div>
</form><p>
	Please send questions or comments to <strong>yunfeigu@usc.edu</strong>
</p>




    </div> <!-- end of main -->
    
    <div id="templatemo_footer">
      <div class="cleaner"></div>
    </div> <!-- end of footer -->
</div>

<div id="templatemo_cr_bar_wrapper">
	<div id="templatemo_cr_bar">
    	Copyright © 2013 <a href="http://genomics.usc.edu">USC Wang Lab</a> | Designed by <a href="http://www.templatemo.com" target="_parent">Free CSS Templates</a>
    </div>
</div>


<script type='text/javascript' src='js/logging.js'></script>
</body>
</html>
