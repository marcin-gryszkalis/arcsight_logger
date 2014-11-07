#!/usr/bin/perl
use strict;
use warnings;
use utf8;

use POSIX qw/strftime/;
my $separator = ' ';

while (<STDIN>)
{
	my $h = undef;

	chomp;
	s/.*?CEF:(\d)/$1/;
	my @cef = split/\|/;
	$h->{CEF_version} = $cef[0];
	$h->{CEF_device_vendor} = $cef[1];
	$h->{CEF_device_product} = $cef[2];
	$h->{CEF_device_version} = $cef[3];
	$h->{CEF_signature_id} = $cef[4];
	$h->{CEF_name} = $cef[5];
	$h->{CEF_severity} = $cef[6];
	$_ = $cef[7];

	my @l1 = split/\s+/;

	my @l = ();
	for my $x (@l1)
	{
		next if $x =~ /^\s*$/;
		if ($x =~ /=/)
		{
			push @l, $x;
			next;
		}

		# no =, append to previous
		my $y = pop @l;
		push(@l, "${y} $x");
	}

	for (@l)
	{
		my @x = split/=/, $_, 2;

		# long timestamp
		if ($x[1] =~ /^\d{13}$/) { $x[1] = $x[1] / 1000; }

		# Unix timestamp
		if ($x[1] =~ /^\d{10}$/) { $x[1] = strftime "%F %T", localtime($x[1]) }

		$h->{$x[0]} = $x[1];
	}

	my @r = ();
	for (@ARGV)
	{
		push(@r,$h->{$_});
	}

	print join($separator, @r)."\n";

}
