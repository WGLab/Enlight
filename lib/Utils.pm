package Utils;

use strict;
use warnings;

sub rndStr
{
    #usage: &rndStr(INT,@stringOfchar)
    #output random string of length INT consisting of characters from @stringOfchar
    join '',@_[ map {rand @_} 1 .. shift ];
}
sub readServConf
{
    my $conf=shift;
    my $install_dir=shift;
    my %param;
    open IN,"<",$conf or die "Cannot open server configuration $conf\n";
    while (<IN>)
    {
	next if /^#|^\s*$/;
	chomp;
	unless (/(.*?)=(.*)/)
	{
	    warn "Malformed configuration\n";
	    return undef;
	}
	my ($key,$value)=($1,$2);
	$key=~s/\s+//g;
	$value=~s/\s+//g;
	if ($param{$key})
	{
	    warn "Duplicate paramter!\n";
	    return undef;
	}
	next unless $key;
	$param{$key}=$value;
    }
    return %param;
}

sub sys_which
{
    my $exe=shift;
    return system("which $exe 1>/dev/null 2>/dev/null") ? 0 : 1;
}

sub listGeneric
{
    #return tables of db, non_generic ones removed
    my $db=shift;
    my @non_generic=@_;
    &sys_which('sqlite3') or die "Cannot find SQLite3\n";
    &sys_which('xargs') or die "Cannot find xargs\n";
    my $table_list=`sqlite3 $db .tables 2>/dev/null | xargs`;
    chomp $table_list;
    map {$table_list =~ s/$_//gi} @non_generic;
    $table_list =~ s/^\s+|\s+$//; #del leading or trailing whitespaces
    return (split /\s+/,$table_list);
}



1;

=head1 Utils

Utils: package with various utilities for downloading, untar,

=head1 SYNOPSIS

use Utils;

 Utils::getstore($url,$file_name,$user,$pass);
 Utils::extract_archive($file,$outfile);
 Utils::config_edit({
 programs        =>      ["P_test","p_postprocess"],
 level           =>      4,
 file            =>      "/home/yunfeiguo/tmp",
 del             =>      15,
 });
 Utils::search_db({
 type => "dbsnp",
 target => $dbsnp,
 build => $buildver,
 version => $dbsnpver,
 install_dir => $install_dir,
 })
 Utils::search($install_dir,"Rscript","local")
 $phred_scheme=Utils::phred_score_check(threshold,readcount,@files);

=head1 AUTHOR

Yunfei Guo

=head1 COPYRIGHT

GPLv3

=cut
