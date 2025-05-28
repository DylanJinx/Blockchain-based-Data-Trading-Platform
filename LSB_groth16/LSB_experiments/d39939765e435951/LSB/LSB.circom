pragma circom 2.1.6;

// include "circomlib/poseidon.circom";
// include "https://github.com/0xPARC/circom-secp256k1/blob/master/circuits/bigint.circom";

// 将 in 转换为 n 位二进制表达
template Num2Bits(n) {
    signal input in;
    signal output out[n];

    var accm = 0;

    for (var i = 0; i < n; i++) {
        out[i] <-- (in \ 2 ** i) % 2;
        accm += out[i]* 2 ** i;
        out[i] * (1 - out[i]) === 0;
    }

    accm === in;
}

// in[0] < in[1] 返回1，否则返回0
template LessThan(n) {
    // 先确定输入信号最多为 2**252 - 1
    assert(n <= 252);
    signal input in[2];
    signal output out;

    component n2b = Num2Bits(n+1);
    n2b.in <== in[0] - in[1] + 2 ** n;
    out <== 1 - n2b.out[n];
}

// 限制 in 最多为 nbits 位
template Range(nbits) {
    signal input in;
    signal bits[nbits];
    var bitsum = 0;
    for (var i = 0; i < nbits; i++) {
        bits[i] <-- (in >> i) & 1;
        bits[i] * (1 - bits[i]) === 0;
        bitsum = bitsum + 2 ** i * bits[i];
    }
	// log("bitsum", bitsum);
    in === bitsum;
}

template IntegerDivide (nbits) {
    assert(nbits <= 126);
    // 被除数
    signal input dividend;
    // 除数
    signal input divisor;
    
    // 余数
    signal output remainder;
    // 商 
    signal output quotient;

    // 限制被除数、除数最多为nbits位
    component range1 = Range(nbits);
    range1.in <== dividend;
    component range2 = Range(nbits);
    range2.in <== divisor;

    // 限制除数不能为0
    signal inv;
    inv <-- 1 / divisor;
    inv * divisor === 1;

    // 计算商和余数
    quotient <-- dividend \ divisor;
    remainder <== dividend - quotient * divisor;

    // 约束余数在范围[0, divisor)之间
    component lessthan = LessThan(nbits);
    lessthan.in[0] <== remainder;
    lessthan.in[1] <== divisor;
    lessthan.out === 1;

    // 约束：正确的计算
    dividend === quotient * divisor + remainder;
}

template ClearLSB() {
    signal input value;
    signal output result;
    signal quotient;

    component integerDivide = IntegerDivide(125);
    integerDivide.dividend <== value;
    integerDivide.divisor <== 2;
    quotient <== integerDivide.quotient;

    // 清除最低位
    result <== quotient * 2;
}


template LSB (numPixels) {
    signal input originalPixelValues[numPixels][3];
    signal input Watermark_PixelValues[numPixels][3];
    signal input binaryWatermark[87];
    signal input binaryWatermark_num;
    //signal t_PixelValues[numPixels][3];

    var Index = 0;
    component clearLSB[numPixels][3];
    
    for (var i = 0; i < 29; i++) {
        for (var j = 0; j < 3; j++) {
            clearLSB[i][j] = ClearLSB();
            clearLSB[i][j].value <== originalPixelValues[i][j];
            // log(clearLSB[i][j].result);
            Watermark_PixelValues[i][j] === clearLSB[i][j].result + binaryWatermark[Index];
            Index = Index + 1;
        }

    }
    binaryWatermark_num === 513;
}

template Main () {
    // signal input width;
    // signal input height;
    // signal numPixels;
    //numPixels <== width * height;
    signal input originalPixelValues[29][3];
    signal input Watermark_PixelValues[29][3];
    signal input binaryWatermark[87];
    signal input binaryWatermark_num;

    component lsb = LSB(29);
    lsb.originalPixelValues <== originalPixelValues;
    lsb.Watermark_PixelValues <== Watermark_PixelValues;
    lsb.binaryWatermark <== binaryWatermark;
    lsb.binaryWatermark_num <== binaryWatermark_num;

}

component main { public [ originalPixelValues ] } = Main();

