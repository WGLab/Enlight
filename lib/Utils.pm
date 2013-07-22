package Utils;

use strict;
use warnings;
use CGI qw/:standard/;
use CGI::Carp qw/fatalsToBrowser/;
use File::Spec;
use Captcha::reCAPTCHA;
use Email::Sender::Simple qw(sendmail);
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

sub error
{
    #usage: &error("message",$logfile,$admin_email)
    #generate a HTML webpage displaying error message, log error and exit
    my $msg=shift || "Unknown error";
    my $log=shift || 'serverlog';
    my $email=shift || 'admin@localhost';
    my $q=new CGI;
    my $output;

    open ERR,'>>',$log or die "Cannot open $log: $!\n";
    $output=$q->header(-status=>'error');
    $output .=$q->start_html(-title=>'Server ERORR');
    $output .=$q->p($msg);
    $output .=$q->p("Please contact $email for help");
    $output .=$q->end_html;
    my $timestamp=`date`;
    chomp $timestamp;
    print ERR "$timestamp\t$msg\n";
    print $output;
    close ERR;
    exit 0;
}

sub generateFeedback 
{
    my $submission_time=scalar localtime;
    print $q->header ("text/html");
    print $q->start_html('Submission status');
    print $q->h1 ("Submission received");
    print $q->p ("Your submission has been received by us at <b>$submission_time</b>.");
    print $q->end_html();
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

    my $email_header
    my $email_body;
    my $email_tail;

    $email_header= "Dear user,\n" 
    $email_header =~ s/(.{1,69})\s/$1\n/g;

    if ($error) 
    {
	$email_body = "We were unable to generate results for your submission due to an '$error' error.\n";
    } else 
    {
	$email_body = "Your submission is done: $url\n\n";
	$email_tail .= "The citation for the above result is: $base_url\n\n";
	$email_tail .= "Questions or comments may be directed to $admin.\n";
	$email_tail =~ s/(.{1,69})\s/$1\n/g;
    }

    return unless $email =~ /.+\@.+\..+/; #User should be responsible for correcting email address
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
    sendmail($message);
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
    print OUT header(),start_html("Result");
    print OUT table($content);
    print OUT end_html();
    close OUT;
}

sub showResult
{
    my $url=shift;
    print redirect($url);
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
