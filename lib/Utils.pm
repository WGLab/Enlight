package Utils;

use strict;
use warnings;
use CGI qw/:standard/;
use File::Spec;
use File::Basename qw/basename/;
#use Captcha::reCAPTCHA;
use Email::Sender::Simple qw(sendmail);
use Email::Sender::Transport::SMTP::TLS; 
use Email::MIME;
use Carp;

sub rndStr
{
    #usage: &rndStr(INT,@stringOfchar)
    #output random string of length INT consisting of characters from @stringOfchar
    join '',@_[ map {rand @_} 1 .. shift ];
}

sub humanCheck
{
    my $private_key=shift;
    my $challenge=shift;
    my $response=shift;
    my $captcha=new Captcha::reCAPTCHA;
    my $recaptcha_result=

    $captcha->check_answer(
	$private_key,$ENV{'REMOTE_ADDR'},
	$challenge,$response );
    return $recaptcha_result->{is_valid};
}

sub readServConf
{
    my $conf=shift;
    my %param;
    open IN,"<",$conf or croak "Cannot open server configuration $conf\n";
    while (<IN>)
    {
	next if /^#|^\s*$/;
	chomp;
	unless (/(.*?)=(.*)/)
	{
	    carp "Malformed configuration\n";
	    return undef;
	}
	my ($key,$value)=($1,$2);
	$key=~s/\s+//g;
	$value=~s/\s+//g;
	if ($param{$key})
	{
	    carp "Duplicate paramter!\n";
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

sub error
{
    #usage: &error("message",$logfile,$admin_email)
    #generate a HTML webpage displaying error message, log error and exit
    my $msg=shift || "Unknown error";
    my $log=shift || 'serverlog';
    my $email=shift || 'admin@localhost';
    my $q=new CGI;
    my $timestamp=scalar localtime;

    open ERR,'>>',$log or die "Cannot open $log: $!\n";
    print ERR "$timestamp\t$msg\n";
    close ERR;
    #show this to user
    $|++;
    print $q->header ("text/html");
    print $q->start_html(-title=>'An error occured');
    print $q->h1 ("Sorry, an error occured...");
    print $q->p ("ERROR:$msg") if $msg;
    print $q->p ("Please refer to help page or contact $email.") if $email;
    print $q->end_html();
    $|--;

    exit 0;
}

sub generateFeedback 
{
    my $result_url=shift;
    my $submission_time=scalar localtime;
    $|++;
    my $q=new CGI;
    print $q->header ("text/html");
    print $q->start_html('Submission status');
    print $q->h1 ("Submission received");
    print $q->p ("Your submission has been received by us at <b>$submission_time</b>.");
    print $q->p("You will be redirected to <a href='$result_url'>result page</a> shortly. Please wait ...");
    print $q->p("If you provided an email address, the result link will be sent to you once analysis is done.");
    print $q->end_html();
    $|--;
}

sub sendEmail
{
    my %hash=%{shift @_};
    my $base_url=$hash{'base_url'} or croak "No base_url";
    my $url=$hash{'url'} or croak "No url";
    my $error;
    $error=$hash{'error'} if $hash{'error'};
    my $email=$hash{'email'} or croak "No user email";
    my $admin=$hash{'admin'} or croak "No admin email";
    my $subject = $hash{'subject'} or croak "No email subject";

    my $email_header;
    my $email_body;
    my $email_tail;

    $email_header= "Dear user,\n";
    $email_header =~ s/(.{1,69})\s/$1\n/g;

    if ($error) 
    {
	$email_body = "We were unable to generate results for your submission due to the following error:\n'$error'";
    } else 
    {
	$email_body = "Your submission is done: $url\n\n";
	$email_tail .= "The citation for the above result is: Guo Y, Conti D V, Wang K. Enlight: web-based integration of GWAS results with biological annotations Bioinformatics, doi: 10.1093/bioinformatics/btu639, 2014\n\n";
	$email_tail .= "Questions or comments may be directed to $admin.\n";
	$email_tail =~ s/(.{1,69})\s/$1\n/g;
    }

    die "Illegal email address\n" unless $email =~ /.+\@.+\..+/; #User should be responsible for correcting email address
    my $message = Email::MIME->create(
	header_str => [
	From    => $admin,
	To      => $email,
	Subject => $subject,
	],
	attributes => {
	    encoding => 'quoted-printable',
	    charset  => 'ISO-8859-1',
	},
	body_str => $email_header.$email_body.$email_tail,
    );

    # sendmail dies on failure, no need for return
    my $transport = Email::Sender::Transport::SMTP::TLS ->new({
	    host => 'smtp.gmail.com',
	    port => 587,
	    username => 'bioinformgroup',
	    password => 'kailab221',
	});
    sendmail($message,{transport=>$transport});
}

sub readObj
{
    #format:1	name:jim	age:23	...
    #omit # lines, must be tab-delimited
    my $file=shift;
    my %hash;
    open IN,'<',$file or die "Can't read $file: $!\n";
    while (<IN>)
    {
	s/\s+$//;
	next if /^#|^\s*$/;
	my @f=split (/\t/,$_,-1);
	next unless @f>1;
	my $id=shift @f;
	$hash{$id}={};
	for my $pair(@f)
	{
	    my ($key,$value)=split (/:/,$pair,-1);
	    next unless $key!~/^\s*$/;
	    $hash{$id}{$key}=$value;
	}
    }
    close IN;
    return %hash;
}

sub genResultPage
{
    #usage: &genResultPage($dir,$url)
    #$dir,$url should point to the same location

    my $dir=shift;
    my $url=shift;
    my $page=File::Spec->catfile($dir,"index.html");
    my @files;
    my $html;

    $url=~s%/*$%%;
    @files=glob File::Spec->catfile($dir,'*');
    if (@files)
    {
	@files=map {basename($_)} @files;
	for my $file(@files)
	{
	    my $link="$url/$file";
	    $html .= 
	    Tr(
		td(
		    p( a({href=>$link},$file) )
		)
	    );
	}
    } else
    {
	$html.=Tr(td("No file found")); 
    }

    open OUT,'>',$page or die "Cannot open $page\n";
    #print OUT header();
    print OUT start_html("Result"); #for generating a html document, header is not required
    print OUT p("Right click and save");
    print OUT table($html);
    print OUT end_html();
    close OUT;
}

sub showResult
{
    my $url=shift;
    print "<META HTTP-EQUIV=refresh CONTENT=\"10;URL=$url\">\n";
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
    my $outfile = shift;

    return 0 unless ($file && $outfile);

    if ($file=~/\.zip$/i && &sys_which("unzip"))
    {
	my $command;
	$command="unzip -p $file > $outfile";
	return !system($command);
    }
    elsif ($file=~/tar\.gz$|\.tgz$|\.bz2?$|\.tbz2?$|\.tar$/i && &sys_which("tar"))
    {
	my $command;
	my $u = scalar getpwuid($>);
	my $g = scalar getgrgid($));
	if($file =~ /\.gz$|\.tgz$/){
	    $command = "tar -zxmO -f $file > $outfile";
	}
	elsif($file =~ /\.bz2?$|\.tbz2?$/){
	    $command = "tar -jxmO -f $file > $outfile";
	}
	elsif ($file=~/\.tar$/) {
	    $command = "tar -xmO -f $file > $outfile";
	}
	$command .= " --owner $u --group $g";
	$command .= " --overwrite";

	return !system($command);
    }
    elsif ($file=~/\.gz$/i && &sys_which("gzip"))
    {
	my $command="gzip -cd $file > $outfile";
	return !system($command);

    }
    else
    {
	warn "Unknown filetype or cannot find gunzip, or tar or unzip, please unpack $file manually\n";
	return 0;
    }
}


sub is_gzip
{
    #check first 2 bytes of input, if 0x1f and 0x8b, return true
    my $in=shift;
    open CHECK,'<',$in or &error("Failed to check whether $in is gzipped: $!");
    read CHECK,my $first,1;
    read CHECK,my $second,1;
    close CHECK;
    #convert string to hex
    $first=ord $first;
    $second=ord $second;
    if ( $first == 0x1f && $second == 0x8b)
    {
	return 1; #gzipped
    } else
    {
	return 0;
    }
}

sub gunzip
{
    my $in=shift;
    my $tmp="/tmp/$$".rand($$).".tmp.gunzip";
    !system("gunzip -c $in > $tmp") or &error("Failed to gunzip $in: $!");
    return $tmp;
}

1;


=head1 Utils

Utils: package with various utilities for displaying results, sending emails etc.

=head1 SYNOPSIS

use Utils;

=head1 AUTHOR

Yunfei Guo

=head1 COPYRIGHT

GPLv3

=cut
