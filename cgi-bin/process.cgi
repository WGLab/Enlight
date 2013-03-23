#!/usr/bin/perl -T

use strict;
use warnings;
use CGI::Pretty;
use CGI::Carp qw/fatalsToBrowser/;

my $q=new CGI::Pretty;
print $q->header;
print $q->start_html,$q->param,$q->end_html;
