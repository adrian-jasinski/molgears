function prefixZeros(number, maxDigits) 
/*dodaje zera przed numerem np  prefixZeros(42, 5) = 00042*/
{  
    var length = maxDigits - number.toString().length;
    if(length <= 0)
    	return number;

    var leadingZeros = new Array(length + 1);
    return leadingZeros.join('0') + number.toString();
}
