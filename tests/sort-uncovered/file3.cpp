int four_bar()
{
int x=1;
int y=2;
return x+y;
}

int four_bar_()
{
int x=1;
if (x)
    return 2*x;     /* This is a really long comment that confirms whether gcovr colors lines that exceed normal expectations. */
else
    return x;
}
