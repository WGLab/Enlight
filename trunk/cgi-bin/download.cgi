#!/usr/bin/perl -w
use strict;
use warnings;
#use Carp;	#there is no need to use Carp, since we will use the Carp defined in the CGI.pm module.
use CGI qw(:standard);
use CGI::Carp qw/fatalsToBrowser/;
my $cgi = new CGI;
my $file = $cgi->param('file');
my $directory = $cgi->param('dir');
my $root = "/var/www/html/annovar-server/html";


  open FILE, "$root/$directory/$file" or die "Can not open the file\n";
  my @file = <FILE>;
  close (FILE);
  print "Content-type: application/x-download\n";
  print "Content-Disposition:attachment;filename="."\""."$file"."\""."\n";
  print "Content-Transfer-Encoding: binary\n";
  print "Content-Length:".`stat -c %s $root/$directory/$file`."\n";
  print "\n\n";
#  open TMP, "$directory/$file" or die "Error message here: $!\n";
#  my @file = <TMP>;
#  close (TMP);

  print @file;
#  binmode TMP;
#  binmode STDOUT;

#print <TMP>;
