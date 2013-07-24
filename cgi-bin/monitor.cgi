#!/usr/bin/env perl

use strict;
use warnings;
use CGI qw/:standard/;
use CGI::Carp qw/fatalsToBrowser/;
use DBI;
use FindBin qw/$RealBin/;
use File::Spec;

use lib File::Spec->catdir($RealBin,"../lib");
use Utils;
use Control;

my %server_conf=&Utils::readServConf(File::Spec->catfile($RealBin,"../conf/enlight_server.conf"))
    or &Utils::error ("Reading server configuration file failed!\n");

my $dbname=$server_conf{'dbname'} || &Utils::error("No MySQL database name\n");
my $dbuser=$server_conf{'dbuser'} || &Utils::error("No MySQL database user\n");
my $dbpassword=$server_conf{'dbpassword'} || &Utils::error("No MySQL database password\n");
my $tablename=$server_conf{'tablename'} || &Utils::error("No table name\n");

#prepare database, it records job status
#job status: (q)ueued, (e)rror, (r)unning, (f)inish, (c)leaned
my $dsn="DBI:mysql:database=$dbname"; #data source name
my $dbh=DBI->connect($dsn,$dbuser,$dbpassword,{
	RaiseError=>1, #report error via die
    	PrintError=>0, #do not report error via warn
    },) or die "Cannot connect: $DBI::errstr\n";

Control->jobMonitor($dbh,$tablename);

$dbh->disconnect();
