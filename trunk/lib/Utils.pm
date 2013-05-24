package Utils;

use strict;
use warnings;
use POSIX;
use File::Copy;
use File::Path;
use File::Find qw/find/;
use File::Spec;
use Cwd;
#use Digest::MD5 qw/md5_hex/;
use Module::Build;


#downloads files from the internet.  Tries to use wget, then curl,
#and finally LWP::Simple
sub md5check
{
    my ($source_file,$md5file)=@_;
    #read MD5 from downloaded file
    open MD5IN,"< $md5file" or warn "CAUTION:Cannot read $md5file, MD5 check failed...\n";
    my @md5in=<MD5IN>;
    close MD5IN;
    open SOURCE,"< $source_file" or warn "CAUTION:Cannot read $source_file, MD5 check failed...\n";
    my $data;
    $data.=$_ while(<SOURCE>);
    close SOURCE;
    my $digest=md5_hex($data);
    $md5in[0]=~/$digest\s+/ ? return 1 : return 0; #assuming only one line input from MD5IN
}

sub getstore 
{
    my $url = shift;
    my $file = shift;
    
    if(&sys_which("wget"))
    {
	my $command = "wget \'$url\' -nd -r -O $file --no-check-certificate";
	return !system($command); 
    }
    elsif(&sys_which("curl"))
    {
	my $command = "curl --connect-timeout 30 -f -L \'$url\' -o $file -C -";
	return !system($command);
    }
    else
    {
	warn "Cannot find wget or curl, please download $file manually\n";
	return 0;
    }
}

#untars a package. Tries to use tar first then moves to the perl package untar Module.
sub extract_archive
{
    my $file = shift;
    my $dir = shift;
    
    return 0 unless ($file && $dir);
    
    my $cwd=cwd;
    chdir($dir);
    
    if ($file=~/\.zip$/ && &sys_which("unzip")) 
    {
	my $command;
	$command="unzip -o $file";
	my $result=!system($command);
	chdir($cwd);
	return $result;
    }
    elsif ($file=~/tar\.gz$|\.tgz$|\.bz2?$|\.tbz2?$|\.tar$/ && &sys_which("tar"))
    {
	my $command;
	my $u = scalar getpwuid($>);
	my $g = scalar getgrgid($));
	if($file =~ /\.gz$|\.tgz$/){
	    $command = "tar -zxm -f $file";
	}
	elsif($file =~ /\.bz2?$|\.tbz2?$/){
	    $command = "tar -jxm -f $file";
	}
	elsif ($file=~/\.tar$/) {
	    $command = "tar -xm -f $file";
	}
	$command .= " --owner $u --group $g";
	$command .= " --overwrite";
	
	my $result=!system($command);
	chdir($cwd);
	return $result;
    }
    elsif ($file=~/\.gz$/ && &sys_which("gunzip"))
    {
	my $command="gunzip -f $file";
	my $result=!system($command);
	chdir($cwd);
	return $result;
    }
    else
    {
	die "Incorrect filename suffix or failed to find gunzip, or tar or unzip, please unpack $file manually\n";
    }

}

#update a download link 
sub update_loc 
{
    my $old_url=shift;
    my $new_url=shift;
    my $loc_file=shift;
    
    open LOC,"< $loc_file" or die "Cannot open $loc_file:$!\n";
    my @tmp;
    while (<LOC>) {
	s/$old_url/$new_url/;
	push @tmp,$_;
    }
    close LOC;
    open LOC,"> $loc_file" or die "Cannot modify $loc_file:$!\n";
    for(@tmp) {
	print LOC;
    }
    close LOC;
    print "Download link list updated.\n";
}

sub down_fail 
{
    my ($url,$loc_file,$file,$dir) = @_;
    
    warn "Download $file failed, update the download link?[N]\n";
    chomp(my $y_n=<STDIN>);
    if ($y_n=~/y/i)
    {
	$y_n=1;
    } 
    else {$y_n=0}

    if ($y_n) 
    {
	warn "Please copy a direct download link here and then press ENTER:\n";
	while (1) 
	{
	    chomp (my $new_url=<>);
	    if ($new_url=~ m%^\w+://%)
	    {
		print STDERR "Updating the link list...";
		&update_loc($url,$new_url,$loc_file);
		print STDERR "Done.\nPlease try to download $file again.[Press ENTER to continue]\n";
		my $tmp=<STDIN>;
		return;
	    }
	    print STDERR "Please enter a valid DIRECT download link.\n";
	}
    } else 
    {
	warn "Please download it manually to $dir\n";
    }
    
}
sub config_edit
{
    #functions: insert new programs at specificied level, options should be manually inserted RIGHT AFTER programs
    ##its function is very limited, make sure you've add levels for each program at first
    ##deletion preceeds insertion
    ##deletion <=1 and insertion <=1 each time
    my $args=shift; #accept a hash reference
    my @program_list=@{$args->{programs}} if defined @{$args->{programs}};
    my $level=$args->{level} if defined @{$args->{level}};	
    my $file=$args->{file} or die "ERROR: No file\n";
    my $del_target=$args->{del} if defined $args->{del};
    my @lines;
    open IN,"<$file" or die "ERROR: Failed to open $file:$!\n";
    @lines=<IN>;
    close IN;
    my $max_level=0;
    for (@lines) {
	($max_level) = $1 if /^(\d+)[pP]/;
    }
    open OUT,">$file" or die "ERROR: Failed to write to $file:$!\n";
    if ($del_target) {
	die "ERROR: level out of range\n" unless $del_target<$max_level && $del_target>0;
	my $current_level=0;
	my $del_toggle=0;
	for my $old(@lines) {
	    next unless defined $old;
	    next if $old=~/(^#)|(^go_)|(^\s)/i;
	    ($current_level)=$1 if $old=~/^(\d+)[pP]/;
	    if ($del_target==$current_level) {
		$old=undef;
		$del_toggle=1;
	    }
	    my $after_del_level=$current_level-1;
	    $old=~s/^\d+/$after_del_level/ if $del_toggle && defined $old;
	    
	}
    }
    my @after_del_lines;
    for (@lines) {
	push @after_del_lines,$_ if defined;
    }
    my @insert_lines;
    if ($level) {
	die "ERROR: Illegal level\n" if $level<1;
	for (@program_list) {
	    push @insert_lines,"$level$_=0\n";
	}
	if ($level>$max_level) {
	    warn "NOTE: level $level goes beyond $max_level, set to $max_level+1 instead\n";
	    $level=$max_level+1;
	    print OUT for (@after_del_lines);
	    print OUT for (@insert_lines);
	} else {
	    my $current_level=0;
	    my $insert_toggle=0;
	    for my $old(@after_del_lines) {
		($current_level)=$1 if $old=~/^(\d+)[pP]/;
		if ($level==$current_level && ! $insert_toggle) {
		    print "got it\n";
		    print OUT for (@insert_lines);
		    $insert_toggle=1;
		}
		if ($insert_toggle) {
		    my $after_insert_level=$current_level+1;
		    $old=~s/^\d+/$after_insert_level/;
		    #fragile, make sure no number before options
		}
		print OUT $old;
	    }
	}
    } else {
	print OUT for (@after_del_lines);
    }
    close OUT;
    return 1;
}

sub search 
{
    my $install_dir = shift;
    my $target=shift;
    my $type=shift;
    $type=$type || "";
    my @list;
    my $path_to_target;
    chomp($path_to_target=`which $target 2>/dev/null`) unless $type=~/local/;
    return $path_to_target if $path_to_target;
    my @search_path=("$install_dir/exe","$install_dir/bin",cwd);
    push @search_path, (split /:/,$ENV{PATH});

    for my $single_path(@search_path)
    {
	find(
	    {
		wanted          => sub { $path_to_target=$File::Find::name and return if ( -f $File::Find::name && /\/$target$/i) },
		no_chdir        => 1,
		bydepth		=> 1,
	    }, $single_path);
	#if multiple targets are found, only the last one will be output
	return $path_to_target if $path_to_target;
    }
    warn "ERROR: Failed to find $target\nPlease use \'cd $install_dir/src\' and then \'./Build installexes\' or add its path to PATH environmental variable\n" and sleep 1;
}
sub abs_path {
    my $exe=shift;
    my $abs_exe;
    if (-l $exe) {
	$abs_exe=readlink $exe;
    } else {
	$abs_exe=$exe;
    }
    return $abs_exe;
}

sub search_db 
{
    #return default database if none supplied
    my $args=shift;
    my $type=$args->{type} or die "No \'type\'";
    my $target=$args->{target} || "";
    my $build=$args->{build} or die "No \'build\'";
    my $version=$args->{version} || "";
    my $install_dir=$args->{install_dir} or die "No \'install_dir\'"; 
    if (! $target) {
	if ($type =~ /ref/) {
	    if ($build eq 'hg19') {
		$target="human_g1k_v37.fasta";
	    } elsif ($build eq 'hg18') {
		$target="human_b36_both.fasta";
	    }
	    $target="$install_dir/database/$target";
	    die "ERROR: No reference genome in $install_dir/database (did you download it?)\n" unless -e $target;
	} elsif ($type =~ /dbsnp/) {
	    $target="$install_dir/database/dbsnp_${build}_$version.vcf";
	    die "ERROR: No dbSNP in $install_dir/database\n" unless -e $target;
	} elsif ($type =~ /hapmap/) {
	    if ($build eq 'hg19') {
		$target ="$install_dir/database/hapmap_3.3.b37.sites.vcf";
	    } elsif ($build eq 'hg18') {
		$target ="$install_dir/database/hapmap_3.3.b36.sites.vcf";
	    }
	    die "ERROR: No HapMap database in $install_dir/database\n" unless -e $target;
	} elsif ($type=~/kg/) {
	    if ($build eq 'hg19') {
		$target="$install_dir/database/1000G_omni2.5.b37.sites.vcf";
	    } elsif ($build eq 'hg18') {
		$target="$install_dir/database/1000G_omni2.5.b36.sites.vcf";
	    }
	    die "ERROR: No 1000g database in $install_dir/database\n" unless -e $target;
	}
	
    }
    return $target;
}
sub install_R_package 
{
    my ($exe_rscript,$package,$libpath)=@_;
    mkdir $libpath unless -d $libpath;
    return ! system("$exe_rscript --vanilla -e 'install.packages(\"$package\",\"$libpath\")'");
    #return ! system("$exe_rscript","--vanilla -e 'install.packages(\"$package\",\"$libpath\",contriburl='http://cran.r-project.org/src/contrib')'");
}

sub phred_score_check
{
    my ($threshold,$readcount,@files)=@_;
    #count bases in 33-58, and 80-104, if # in first bin exceeds $threshold, phred33, # in second bin exceeds threshold, phred64, otherwise, error
    my @phred64;
    my @phred33;
    my $count35; # counts bases in 33-58
    my $count64; # counts bases in 80-104

    for my $fq (@files)
    {

	open my $fh, '<', $fq or die "Cannot read $fq: $!\n"; 
	while (<$fh>)
	{
	    next unless $. % 4==0; #current line number
	    chomp;
	    $count35 +=  () = /[!"#$%&'()*+,\-.\/0123456789:]/g;
	    $count64 +=  () = /[\@P-Z\[\\\]^_`abcdefgh]/g;
	    #warn "$_: $count35,$count64\n";
	    last if $.>$readcount*4;

	}
	close $fh;

	#warn "$fq $readcount reads have $count35 phred35 scocres, $count64 phred64 scores\n";
	if ($count35>$threshold && $count64 > $threshold)
	{
	    die "ERROR: phred64 and phred33 scores are both present\n";
	}
	elsif ($count35>$threshold && $count64<=$threshold)
	{
	    push @phred33,$fq;
	}
	elsif ($count35<=$threshold && $count64 > $threshold)
	{
	    push @phred64,$fq;
	}
	else
	{
	    die "ERROR: phred64 and phred33 scores are both absent\n"; 
	}
    }

    if (@phred64==@files)
    {	return 64   }
    elsif (@phred33==@files)
    {	return 33    }
    else 
    {
	warn "@phred64 are Phred64 encoded\n@phred33 are Phred33 encoded\n";
	die "ERROR: All FASTQ files must have the same Phred score scheme\n";
    }
}
sub sys_which
{
    my $exe=shift;
    return system("which $exe 1>/dev/null 2>/dev/null") ? 0 : 1;
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
	$value=~s/^install_dir/$install_dir/;
	if ($param{$key})
	{
	    warn "Duplicate paramter!\n";
	    return undef;
	}
	unless ( ($key && $value) )
	{
	    warn "Missing parameter or its value\n";
	    return undef;
	}
	$param{$key}=$value;
    }
    return %param;
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
