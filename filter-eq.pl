#!/usr/bin/perl
use POSIX qw/strftime/;

my $separator = ' ';

while (<STDIN>)
{
	my @l1 = split/\s+/;

	my @l = ();
	for my $x (@l1)
	{
		if ($x =~ /=/)
		{
			push @l, $x;
			next;
		}

		# no =, append to previous
		$y = pop @l;
		push(@l, "${y} $x");
	}

	for (@l)
	{
		@x = split/=/, $_, 2;

		# long timestamp
		if ($x[1] =~ /^\d{13}$/) { $x[1] = $x[1] / 1000; }

		# Unix timestamp
		if ($x[1] =~ /^\d{10}$/) { $x[1] = strftime "%F %T", localtime($x[1]) }

		$h->{$x[0]} = $x[1];
	}

	@r = ();
	for (@ARGV)
	{
		push(@r,$h->{$_});
	}

	print join($separator, @r)."\n";

}