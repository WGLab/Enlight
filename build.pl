#!/usr/bin/env perl
use strict;
use warnings;

die "Usage: $0 <perl_path>\n" unless @ARGV == 1;
my $my_perl_path = shift @ARGV;
my @all_files = `find . -name '*'`;
chomp @all_files;
my $count = 0;
for my $file(@all_files) {
	next unless -f $file and -w $file;
	my $first_line = `head -n1 $file`;
	if ($first_line=~/^#!/ and $first_line=~/perl/) {
		#this is a perl script
		warn "processing $file\n";
		$count++;
		!system("perl -i -pe 'if(\$.==1){s%.*%#!$my_perl_path%;}' $file") or die "$!\n";
	}
}
warn "done scanning ",scalar @all_files," files\n";
warn "done modifying $count perl scripts.\n";
