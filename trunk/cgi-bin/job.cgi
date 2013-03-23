#!/usr/bin/perl -w
use strict;
use warnings;
#use Carp;	#there is no need to use Carp, since we will use the Carp defined in the CGI.pm module.
use CGI qw(:standard);
use CGI::Carp qw/fatalsToBrowser/;



my $dir="/var/www/html/annovar-server/exec/work";
#my $dir="/var/www/html/annovar-server/html/done";

#chdir($dir);
my (@id, @time, @usr, @email, %info, $content, $type, @stat);
opendir(DH, "$dir") or die "Can't open: $!\n" ;

foreach (sort readdir(DH)) {
if ($_ eq '.' || $_ eq '..') {
next;
}
my $fd = $_;
if (-d "$dir/$_"){
push @id, $_;
open (INFO, "$dir/$_/info") or warn "Error: cannot read info file $dir/$_/info: $!";
while (<INFO>) {
        chomp;
        my ($key, $value) = split ('=', $_);
        $info{$key} = $value;
}
close (INFO);
push @time, $info{submission_time};
push @usr, $info{sample_id};
push @email, $info{reply_email};
if (-f "$dir/$fd/query.output.exonic_variant_function") {
$type= "running";
}else{
$type="queued";
}
push @stat, $type;
}
}

closedir(DH);




for (my $i=0; $i<@id; $i++) {
#    print "$id[$i].\t.$time[$i].\t.$usr[$i].\t.$email[$i]\n";
$content .= "<tr><td>$id[$i]</td><td>$time[$i]</td><td>$usr[$i]</td><td>$stat[$i]</td></tr>"; ###
}

my $heade = qq(
<html xmlns="http://www.w3.org/1999/xhtml" lang="en-US" xml:lang="en-US"><head><meta http-equiv="Content-Type" content="text/html; charset=ISO-8859-1">
<title>submissions</title>
<link rel="stylesheet" type="text/css" href="http://wannovar.usc.edu/annovar.css" media="screen">
</head><body>);

print "Content-type: text/html\n\n";
print ($heade.qq(<table class="sortable" width="750"><thead><tr> <th width="120"> Submission ID </th> <th width="215"> Submission time </th> <th width="250"> Sample identifier </th><th width="200">Running status</th></tr></thead>$content</table></body></html>));
