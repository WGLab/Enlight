#!/usr/bin/perl
use warnings;
use strict;
use CGI;

#my $submission = $ARGV[0];
#my $dir = "/var/www/html/annovar-server/exec/work/$submission"; 

##################################################################################
my $q = new CGI;
my $sort = $q->param('select');

my $segdup = $q->param('SegDup');
my $segdupv = $q->param('SegDupv');
my $kgall = $q->param('1000g2010nov_ALL');
my $kgallv = $q->param('1000g2010nov_ALLv');
my $kgceu = $q->param('1000g2010jul_CEU');
my $kgceuv = $q->param('1000g2010jul_CEUv');
my $kgyri = $q->param('1000g2010jul_YRI');
my $kgyriv = $q->param('1000g2010jul_YRIv');
my $kgjptchb = $q->param('1000g2010jul_JPTCHB');
my $kgjptchbv = $q->param('1000g2010jul_JPTCHBv');
my $sift = $q->param('SIFT');
my $siftv = $q->param('SIFTv');
my $polyp2 = $q->param('PolyPhen2');
my $polyp2v = $q->param('PolyPhen2v');
my $ljbmt = $q->param('LJB_MutationTaster');
my $ljbmtv = $q->param('LJB_MutationTasterv');
my $ljbp = $q->param('LJB_PhyloP');
my $ljbpv = $q->param('LJB_PhyloPv');
my $ljblrt = $q->param('LJB_LRT');
my $ljblrtv = $q->param('LJB_LRTv');
my $gerp = $q->param('LJB_GERP');
my $gerpv = $q->param('LJB_GERPv');
my $dbsnp = $q->param('dbSNP');
my $chr = $q->param('Chr');
my $gene = $q->param('Gene');
my $pg = $q->param('page');
my $submission = $q->param('submission');
my $file = $q->param('file');
my $tle = $q->param('title');
my $buildver = $q->param('buildver');
my $dir = "/var/www/html/annovar-server/html/done/$submission";

my %list = (
ex1=> "exonic",
ex2=> "exonic;splicing",
ex3=> "splicing",
UTR3=>"UTR3",
UTR5=>"UTR5",
intr=>"intronic",
inter=>"intergenic",
up=>"upstream",
dn=>"downstream",
updn=>"upstream;downstream",
ncex=>"ncRNA_exonic",
ncin=>"ncRNA_intronic",
nc3=>"ncRNA_UTR3",
nc5=>"ncRNA_UTR5",
FI=>"frameshift insertion",
FD=>"frameshift deletion",
NFD=>"nonframeshift deletion",
NFI=>"nonframeshift insertion",
NSV=>"nonsynonymous SNV",
SV=>"synonymous SNV",
SPV=>"stopgain SNV",
SPL=>"stoploss SNV",
UK=>"unknown",
);

my %mark = (
"gt"=>">",
"lt"=>"<",
"eq"=>"=",
"ge"=>">=",
"le"=>"<=",
);

# the sub routine proc read the file name and webpage title, and return the dynamic webpage
&proc($file,$tle); #&proc("query.output.genome_summary.csv","genome_filtering_results");

sub proc {
my $title;
my @line1;
my $content;
my ($fl, $fe) = @_;

my $heade = qq(
<html xmlns="http://www.w3.org/1999/xhtml" lang="en-US" xml:lang="en-US"><head><meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
<title>$fe</title>
<link rel="stylesheet" type="text/css" href="http://wannovar.usc.edu/annovar.css" media="screen">
</head>);

chdir($dir);

open EX, "$fl" or die"can't open file $fl";
my $form = qq{<b>Sort by:</b><select name="select"><option value=""></option>}; #$form store the HTML code for Sorting component
my $filter = qq(<h2><b>Filter by:</b></h2>); #$filter store the HTML code for Filter component
my (@numline, @numlinesn, @ifline, @chrline, $gerpnum, $dbsnpnum, @ljb, @numprt, @ifljb);
 
while(<EX>) {
 chomp $_;
 @line1 = split /,/, $_; #read the first line of the file and automatically detect the names of columns, store them in @line1	
 	@numline = ($buildver eq "hg19") ? (5,6,7,9,10,12,14,16,18,20) : (5..9,11,12,14,16,18,20,22); #exclude Start End
 	@numlinesn = ($buildver eq "hg19") ? (5,6,7,9,22,23) : (5..9,11,24,25); #
 	@ifline = ($buildver eq "hg19") ? (4,8) : (4,10);
 	@ifljb = ($buildver eq "hg19") ? (7) : (7..9);
 	@chrline = ($buildver eq "hg19") ? (1,21) : (1,23);
 	$gerpnum = ($buildver eq "hg19") ? 20 : 22;
  $dbsnpnum = ($buildver eq "hg19") ? 8 : 10;
  @numprt = ($buildver eq "hg19") ? (6,10,14,16,18) : (6,12,16,18,20);
  @ljb = ($buildver eq "hg19")?(10,12,14,16,18,20):(12,14,16,18,20,22);
# my $dbsnp = ($buildver eq "hg19") ? "dbSNP135" : "dbSNP132";
my $tt1 = qq(<table class="sortable" cellspacing="1" cellpadding="3" border="0"><thead><tr valign="top">);#HTML code for main table
my $tt;#HTML code for main table
foreach (@line1){
my $tlle = $_;
   $tlle =~ tr/\_/ / ;	
$tt .= qq(<th align="LEFT" class=""><tt> $tlle </tt></th>);
if ($_ eq "LJB_GERP++") {
if ("LJB_GERP" eq $sort) {
$form .= qq(<option value="LJB_GERP" selected>LJB_GERP++</option>);
}
else{
$form .= qq(<option value="LJB_GERP">LJB_GERP++</option>);
}	
}
else {
if ($_ eq $sort) {
$form .= qq(<option value="$_" selected>$_</option>);
}
else{
$form .= qq(<option value="$_">$_</option>);
}
}	
}

$filter .= qq(<table border="0" cellspacing="1" cellpadding="1"><tbody>);
my $mk = 0;

# process the numeric column
foreach my $t (@line1[@numline]){
my $tp = $t."v";
$mk++;
if (($mk%3)==1) {
$filter .= "<tr>";	
}
if ($t eq "LJB_GERP++"){
$filter .= qq(<td valign="baseline"><p>LJB_GERP++: <a href="http://wannovar.usc.edu/tutorial.html#LJB_GERP" target="_blank"><img src="http://wannovar.usc.edu/images/intero.png" alt="" width="20" height="20" border="0"/></a></p></td><td valign="baseline"><select name="LJB_GERP">                                   
    <option value=""></option>); 
foreach ("gt","lt","eq","ge","le") {   
	if ($_ eq $q->param("LJB_GERP")) {                                             
  $filter .= qq(<option value=$_ selected>).$mark{$_}.qq(</option>);   
  }
  else{
  $filter .= qq(<option value=$_>).$mark{$_}.qq(</option>);  
  }
  }                                                    
  $filter .= qq(</select><input type="text" size=8 name="LJB_GERPv" value=").$q->param("LJB_GERPv").qq("/></td>);
}
else {
$filter .= qq(<td valign="baseline"><p>$t: <a href="http://wannovar.usc.edu/tutorial.html#$t" target="_blank"><img src="http://wannovar.usc.edu/images/intero.png" alt="" width="20" height="20" border="0"/></a></p></td><td valign="baseline"><select name="$t">
    <option value=""></option>);
    
 foreach ("gt","lt","eq","ge","le") {   
	if ($_ eq $q->param($t)) {                                             
  $filter .= qq(<option value=$_ selected>).$mark{$_}.qq(</option>);   
  }
  else{
  $filter .= qq(<option value=$_>).$mark{$_}.qq(</option>);  
  }
}  
  $filter .= qq(</select><input type="text" size=8 name="$tp" value =" ).$q->param($tp).qq("/></td>);
}
if (($mk%3)==0) {
$filter .= "</tr>";	
}	
}

#process the Chr Gene column
$filter .= qq(</tbody></table><table cellspacing="1" cellpadding="3" border="0"><tr><td>Chr:&nbsp;&nbsp; <input type="text" name="Chr" value="$chr" size=8/> </td></tr>);

#start end
foreach my $t ("Start","End"){
my $tp = $t."v";	
if ($t eq "Start"){
$filter .= qq(<tr><td><p>$t: <select name="$t">
    <option value=""></option>);
}
else{
$filter .= qq(<tr><td><p>$t:&nbsp;&nbsp; <select name="$t">
    <option value=""></option>);
}

    
 foreach ("gt","lt","eq","ge","le") {   
	if ($_ eq $q->param($t)) {                                             
  $filter .= qq(<option value=$_ selected>).$mark{$_}.qq(</option>);   
  }
  else{
  $filter .= qq(<option value=$_>).$mark{$_}.qq(</option>);  
  }
}  
  $filter .= qq(</select><input type="text" size=8 name="$tp" value =" ).$q->param($tp).qq("/></p></td></tr>);
}
# gene
$filter .= qq(<tr><td>Gene: <input type="text" name="Gene" value="$gene" size=8/> </td></tr>);

#process the yes or no column
foreach my $t (@line1[@ifline]){
    $filter .= qq(<tr><td>$t: <a href="http://wannovar.usc.edu/tutorial.html#$t" target="_blank"><img src="http://wannovar.usc.edu/images/intero.png" alt="" width="20" height="20" border="0"/></a> <select name="$t">
    <option value=""></option>);
    foreach ("yes","no") {
    if ($_ eq $q->param($t)) {
    $filter .= qq(<option value="$_" selected>$_</option>); 
    }
    else {
    $filter .= qq(<option value="$_">$_</option>); 
    }
    }
    $filter .= qq(</select></td></tr>);
}

foreach my $t (@line1[@ifljb]){
	  my $tp = $t."j";
    $filter .= qq(<tr><td>$t: <a href="http://wannovar.usc.edu/tutorial.html#$t" target="_blank"><img src="http://wannovar.usc.edu/images/intero.png" alt="" width="20" height="20" border="0"/></a> <select name="$tp">
    <option value=""></option>);
    foreach ("yes","no") {
    if ($_ eq $q->param($tp)) {
    $filter .= qq(<option value="$_" selected>$_</option>); 
    }
    else {
    $filter .= qq(<option value="$_">$_</option>); 
    }
    }
    $filter .= qq(</select></td></tr>);
}
#process the Func column
$filter .= qq(</tbody></table><table cellspacing="1" cellpadding="3" border="0"><tr><td>Func: <a href="http://wannovar.usc.edu/tutorial.html#Func" target="_blank"><img src="http://wannovar.usc.edu/images/intero.png" alt="" width="20" height="20" border="0"/></a><br>);
foreach ("ex1","ex2","ex3","UTR3","UTR5","intr","inter","up","dn","updn","ncex","ncin","nc3","nc5") {	
my $flag = 0;
foreach my $r ($q->param("Func")) {	
if ($_ eq $r) {
	$flag = 1;
}
}
if ($flag==1) {
$filter .= qq(<input type="checkbox" name="Func" value ="$_" checked>$list{$_}<br>);	
}
else {
$filter .= qq(<input type="checkbox" name="Func" value ="$_" >$list{$_}<br>);
}
}
$filter .= qq(</td>);

#process the ExonicFunc column
$filter .= qq(<td valign="top">ExonicFunc: <a href="http://wannovar.usc.edu/tutorial.html#ExonicFunc" target="_blank"><img src="http://wannovar.usc.edu/images/intero.png" alt="" width="20" height="20" border="0"/></a><br>);
foreach ("FI","FD","NFD","NFI","NSV","SV","SPV","SPL","UK") {  
my $flag = 0;
foreach my $r ($q->param("ExonicFunc")) {		
if ($_ eq $r) {
	$flag = 1;	
}
}
if ($flag==1) {
$filter .= qq(<input type="checkbox" name="ExonicFunc" value ="$_" checked>$list{$_}<br>);	
}
else {
$filter .= qq(<input type="checkbox" name="ExonicFunc" value ="$_" >$list{$_}<br>);
}
}
$filter .= qq(</td></tr>);
$filter .="</tbody></table>";

#process the hide information
$filter .= qq(<p><input type="text" size=10 name="buildver" value = $buildver  style= "display:none"/></p>);
$filter .= qq(<p><input type="text" size=10 name="page" id = "fname" value = 1  style= "display:none"/></p>);
$filter .= qq(<p><input type="text" size=10 name="submission"  value = $submission  style= "display:none"/></p>);
$filter .= qq(<p><input type="text" size=10 name="file"  value = $file  style= "display:none"/></p>);
$filter .= qq(<p><input type="text" size=10 name="title"  value = $tle  style= "display:none"/></p>);
$filter .= qq(<p><input type="submit" value="Go" /></p>);

my $tt2 = qq(</tr></thead>);#HTML code for main table
$title = $tt1.$tt.$tt2; #HTML code for main table, combine $tt1 $tt $tt2
last;
}


#readline EX;    # skip the first line 

my $rec=0;
my @array = ();
while (<EX>) { #the first line has been skipped already
chomp $_;
push @array, $_;
}

##sort the table
my %hash = &sort_hd($fl);

unless ($sort eq "") {
@array=();
my @st;
if ($sort =~ /Func|Gene|AAChange|dbSNP|Pred|Chr|Start|End|Ref|Obs|Otherinfo/) {#sort numeric
 @st = sort (keys %{%hash->{$sort}});
}
else {
 @st = sort {$a<=>$b} (keys %{%hash->{$sort}});
}
foreach (@st) {
push @array, @{%hash->{$sort}{$_}};
}
}

##filter the table
my @ay = &sort_ad(@array);
$line1[$gerpnum] =~ tr/\+//d; #
@array=();
LINE: for (my $k1 = 0; $k1<=$#ay; $k1++){

##check box: Func, ExonicFunc
for my $k2 (0,2){
my @tp = $q->param($line1[$k2]);	
unless (@tp) {next;} 
my $flag = 0;
foreach (@tp) {
if (@ay->[$k1][$k2] eq $list{$_}) {
$flag = 1;
}
}
 if ($flag==0) { next LINE;
	}
}

## select: AAChange, Conserved, dbSNP130
for my $k2 (@ifline){
my $tmp = $q->param($line1[$k2]);	
if (($tmp eq "no") and (@ay->[$k1][$k2] ne "")) {
	next LINE;
}
elsif (($tmp eq "yes") and (@ay->[$k1][$k2] eq "")) {
  next LINE;
}
}

for my $k2 (@ifljb){
my $tmp = $q->param($line1[$k2]."j");	
if (($tmp eq "no") and (@ay->[$k1][$k2] ne "")) {
	next LINE;
}
elsif (($tmp eq "yes") and (@ay->[$k1][$k2] eq "")) {
  next LINE;
}
}

## input: Chr, Gene
for my $k2 (@chrline){
my $tmp = $q->param($line1[$k2]);
if ($tmp eq "") {next;}
if ((uc $tmp) ne uc (@ay->[$k1][$k2])) {
  next LINE;
}
}

## numeric
for my $k2 (@numlinesn){
my $tp1 = $q->param($line1[$k2]);
my $tp2 = $q->param($line1[$k2]."v");
if (($tp1 eq "ge") and ($tp2 > @ay->[$k1][$k2])) {
  next LINE;
}
elsif (($tp1 eq "gt") and ($tp2 >= @ay->[$k1][$k2])) {
  next LINE;
}
elsif (($tp1 eq "lt") and ($tp2 <= @ay->[$k1][$k2])) {
  next LINE;
}
elsif (($tp1 eq "le") and ($tp2 < @ay->[$k1][$k2])) {
  next LINE;
}
elsif (($tp1 eq "eq") and ($tp2 != @ay->[$k1][$k2])) {
  next LINE;
}
}

##@ljb 
for my $k2 (@ljb){
my $tp1 = $q->param($line1[$k2]);
my $tp2 = $q->param($line1[$k2]."v");

if (($tp1 eq "ge") and (($tp2 > @ay->[$k1][$k2]) and (@ay->[$k1][$k2] ne "")) ) {
  next LINE;
}
elsif (($tp1 eq "gt") and (($tp2 >= @ay->[$k1][$k2]) and (@ay->[$k1][$k2] ne ""))) {
  next LINE;
}
elsif (($tp1 eq "lt") and ($tp2 <= @ay->[$k1][$k2]) ) {
  next LINE;
}
elsif (($tp1 eq "le") and ($tp2 < @ay->[$k1][$k2])) {
  next LINE;
}
elsif (($tp1 eq "eq") and ($tp2 != @ay->[$k1][$k2])) {
  next LINE;
}
}

my @ln = ();

for my $k2 (0..$#line1) {
push @ln, @ay->[$k1][$k2];
}
my $line = join ("<=>",@ln);

push @array , $line; 
}

#print @array;
my $page = "Page:&nbsp;"; 
my $pflag = @array/100 + 1;


for (my $k=1; $k < $pflag; $k++) {

#$page .= qq(<a href="$ft$k.html">$g</a>&nbsp;);
$page .= qq(<a href="javascript:fm.submit();" onclick=document.getElementById("fname").value=$k>$k</a>&nbsp;);
}



my $cntpage=0;
my $mkpage=100;
if (@array<100) {
$mkpage = @array;
}

foreach (@array) {
$cntpage++;
next if ($cntpage<=($pg-1)*100);

#/\"(.*?)\"\,\"(.*?)\"\,(.*)/;

my @tp = split /<=>/, $_;
#$content .= qq(<tr valign="top"> <td><tt> $1 </tt></td> <td><tt> $2 </tt></td> <td><tt> $tp[0] </tt></td> <td><tt> $tp[1] </tt></td><td><tt> $tp[2] </tt></td> <td><tt> $tp[3] </tt></td> <td><tt> $tp[4] </tt></td> <td><tt> $tp[7] </tt></td > <td><tt> $tp[8] </tt></td> <td><tt> $tp[9] </tt></td> <td><tt> $tp[10] </tt></td> <td><tt> $tp[11] </tt></td > <td><tt> $tp[12] </tt></td> <td><tt> $tp[13] </tt></td> <td><tt> $tp[14] </tt></td > <td><tt> $tp[15] </tt></td> <td><tt> $tp[16] </tt></td> <td><tt> $tp[17] </tt></td> <td><tt> $tp[18] </tt></td> </tr>);
#$content .= qq(<tr valign="top"> <td><tt> $1 </tt></td> <td><tt> $2 </tt></td>);
$content .= qq(<tr valign="top">);


foreach my $j (@numprt) {
  unless($tp[$j] eq "") {
  $tp[$j] = sprintf ("%.3g", $tp[$j]);
}
}


for (my $i = 0; $i < @line1; $i++){
$tp[$i] =~ tr/\"//d; 
if ($i==4 and ($tp[$i]=~ /lod\=\d+/)) {
$tp[$i] = $&; 
$tp[$i]=~ tr/lod\=//d;
}

$tp[$i] =~ s/\(.+\)//g;		#get rid of the parenthesis for splicing mutations

if ($i==1) {
if ($tp[$i] =~ /(^\w+)([\,|\;|\(].*)/){
$content .= qq(<td><tt><a href="http://genome.ucsc.edu/cgi-bin/hgTracks?org=human&singleSearch=knownCanonical&position=$1" target="_blank">$1</a>$2</tt></td>);	
}else{
$content .= qq(<td><tt><a href="http://genome.ucsc.edu/cgi-bin/hgTracks?org=human&singleSearch=knownCanonical&position=$tp[$i]" target="_blank">$tp[$i]</a></tt></td>);	
}
}
elsif ($i==$dbsnpnum) {
$content .= qq(<td><tt><a href="http://www.ncbi.nlm.nih.gov/snp/?term=$tp[$i]">$tp[$i]</a></tt></td>);
}
else {
$content .= qq(<td><tt> $tp[$i] </tt></td>);
}
}
$content .= qq(</tr>);  

$rec++;
if ($rec==$mkpage) {
last;
}
}
print "Content-type: text/html\n\n";
print qq($heade<body class="results"><p>100 results per page</p><p><a href="http://wannovar.usc.edu/">back to HOME</a></p><b>$page</b><pre>$title)."<tbody>".qq($content</tbody></table></pre><p><b>$page</b></p><hr><form method="post" name=fm action=http://wannovar.usc.edu/cgi-bin/web_result_filter_dev.pl><h2>$form</select></h2><br>$filter</form></body></html>);

close(EX);
}
#print "Content-type: text/html\n\n";

####################
####################

# generate hash data structure for sorting
sub sort_hd {
my ($fln) = @_;
my $dat={};
my @col;
my @cont;
open (FL, "$fln") or die "can not open file $fln";

while(<FL>){
chomp $_;
push @cont, $_;
}
close (FL);
  $cont[0] =~ tr/\+//d;
  @col = split /,/, $cont[0];
#  readline FL;    # skip the first line 
shift (@cont) ;
    for (my $k=0; $k<@col; $k++){
        foreach (@cont) {
        chomp $_;
        /\"(.*?)\"\,\"(.*?)\"\,(.*)/;
    my $t = $3;
    $t =~ tr/\"//d;
    my @tp = split /,/, $t;
        @tp = ($1,$2,@tp);
       # push @{$dat->{$col[$k]}},$tp[$k].$_;
        push @{$dat->{$col[$k]}{$tp[$k]}},$_;
        }
 }
return %{$dat};
}

# generate array data structure for filing
sub sort_ad {
my (@cont) = @_;
my $dat=[];
my $k=0;
#   shift (@cont) ;
   for (my $k=0; $k<@cont; $k++){
        chomp $cont[$k];
    $cont[$k] =~  /\"(.*?)\"\,\"(.*?)\"\,(.*)/;
    my $t = $3;
    $t =~ tr/\"//d;
    my @tp = split /,/, $t;
        @tp = ($1,$2,@tp);
        #push @{$dat->{$col[$k]}},$tp[$k].$_;
        foreach (@tp) {
        push @{$dat->[$k]},$_;
      }
 }
close (FL);
return @{$dat};
}
