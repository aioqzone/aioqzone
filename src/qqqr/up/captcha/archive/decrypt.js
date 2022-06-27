function hex2int(hex) {
    var len = hex.length, a = new Array(len), code;
    for (var i = 0; i < len; i++) {
        code = hex.charCodeAt(i);
        if (48 <= code && code < 58) {
            code -= 48;
        } else {
            code = (code & 0xdf) - 65 + 10;
        }
        a[i] = code;
    }

    return a.reduce(function (acc, c) {
        acc = 16 * acc + c;
        return acc;
    }, 0);
}
function Base64() {
    // private property
    this._keyStr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
}
function strToLongs(s) {
    var l = new Array(Math.ceil(s.length / 4));
    for (var i = 0; i < l.length; i++) {
        // note little-endian encoding - endianness is irrelevant as long as
        // it is the same in longsToStr()
        l[i] = s.charCodeAt(i * 4) + (s.charCodeAt(i * 4 + 1) << 8) +
            (s.charCodeAt(i * 4 + 2) << 16) + (s.charCodeAt(i * 4 + 3) << 24);
    }
    return l;  // note running off the end of the string generates nulls since
}
function longsToStr(l) {  // convert array of longs back to string
    var a = new Array(l.length);
    for (var i = 0; i < l.length; i++) {
        a[i] = String.fromCharCode(l[i] & 0xFF, l[i] >>> 8 & 0xFF,
            l[i] >>> 16 & 0xFF, l[i] >>> 24 & 0xFF);
    }
    return a.join('');  // use Array.join() rather than repeated string appends for efficiency in IE
}
Base64.prototype.encode = function (input) {
    var output = "", chr1, chr2, chr3, enc1, enc2, enc3, enc4, i = 0;
    //input = this._utf8_encode(input);
    while (i < input.length) {
        chr1 = input.charCodeAt(i++);
        chr2 = input.charCodeAt(i++);
        chr3 = input.charCodeAt(i++);
        enc1 = chr1 >> 2;
        enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
        enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
        enc4 = chr3 & 63;
        if (isNaN(chr2)) {
            enc3 = enc4 = 64;
        } else if (isNaN(chr3)) {
            enc4 = 64;
        }
        output = output +
            this._keyStr.charAt(enc1) + this._keyStr.charAt(enc2) +
            this._keyStr.charAt(enc3) + this._keyStr.charAt(enc4);
    }
    return output;
}

Base64.prototype.decode = function (input) {
    var output = [], chr1, chr2, chr3, enc1, enc2, enc3, enc4, i = 0;
    input = input.replace(/[^A-Za-z0-9\+\/\=]/g, "");
    while (i < input.length) {
        enc1 = this._keyStr.indexOf(input.charAt(i++));
        enc2 = this._keyStr.indexOf(input.charAt(i++));
        enc3 = this._keyStr.indexOf(input.charAt(i++));
        enc4 = this._keyStr.indexOf(input.charAt(i++));
        chr1 = (enc1 << 2) | (enc2 >> 4);
        chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
        chr3 = ((enc3 & 3) << 6) | enc4;
        output.push(String.fromCharCode(chr1));
        if (enc3 != 64) {
            output.push(String.fromCharCode(chr2));
        }
        if (enc4 != 64) {
            output.push(String.fromCharCode(chr3));
        }
    }
    //output = this._utf8_decode(output);
    return output.join("");
}

function EncryptBlock(EncryData, Key) {
    var x = EncryData[0];
    var y = EncryData[1];
    var sum = 0;
    var delta = 0x9E3779B9;
    for (var i = 0; i < 32; i++) {
        if (((sum & 3) == Key[6])) {
            x += (((y << 4) ^ (y >>> 5)) + y) ^ (sum + Key[sum & 3] + Key[4]);
        } else if ((sum & 3) == Key[7]) {
            x += (((y << 4) ^ (y >>> 5)) + y) ^ (sum + Key[sum & 3] + Key[5]);
        } else {
            x += (((y << 4) ^ (y >>> 5)) + y) ^ (sum + Key[sum & 3]);
        }
        sum += delta;
        if (((sum >> 11) & 3) == Key[6]) {
            y += (((x << 4) ^ (x >>> 5)) + x) ^ (sum + Key[(sum >> 11) & 3] + Key[4]);
        } else if (((sum >> 11) & 3) == Key[7]) {
            y += (((x << 4) ^ (x >>> 5)) + x) ^ (sum + Key[(sum >> 11) & 3] + Key[5]);
        } else {
            y += (((x << 4) ^ (x >>> 5)) + x) ^ (sum + Key[(sum >> 11) & 3]);
        }
    }
    return [x, y];
}
function DecryptBlock(DecryData, Key) {
    var x = DecryData[0];
    var y = DecryData[1];
    var sum = 0x9E3779B9 * 32;
    var delta = 0x9E3779B9;
    for (var i = 0; i < 32; i++) {
        if (((sum >> 11) & 3) == Key[6]) {
            y -= (((x << 4) ^ (x >>> 5)) + x) ^ (sum + Key[(sum >> 11) & 3] + Key[4]);
        } else if (((sum >> 11) & 3) == Key[7]) {
            y -= (((x << 4) ^ (x >>> 5)) + x) ^ (sum + Key[(sum >> 11) & 3] + Key[5]);
        } else {
            y -= (((x << 4) ^ (x >>> 5)) + x) ^ (sum + Key[(sum >> 11) & 3]);
        }
        sum -= delta;
        if (((sum & 3) == Key[6])) {
            x -= (((y << 4) ^ (y >>> 5)) + y) ^ (sum + Key[sum & 3] + Key[4]);
        } else if ((sum & 3) == Key[7]) {
            x -= (((y << 4) ^ (y >>> 5)) + y) ^ (sum + Key[sum & 3] + Key[5]);
        } else {
            x -= (((y << 4) ^ (y >>> 5)) + y) ^ (sum + Key[sum & 3]);
        }

    }
    return [x, y];
}
var teaDecrypt = function (msg, Key) {
    var res = new Base64().decode(msg);
    var rounds = res.length >> 3;
    var tmp;
    var final = "";
    for (var i = 0; i < rounds; i++) {
        tmp = DecryptBlock(strToLongs(res.slice(i * 8, i * 8 + 8)), Key);
        final += longsToStr(tmp);
    }
    return final;
}
function teaEncrypt(msg, Key) {
    var final = "";
    var rounds = msg.length >> 3;
    for (var i = 0; i < rounds; i++) {
        tmp = EncryptBlock(strToLongs(msg.slice(i * 8, i * 8 + 8)), Key);
        final += longsToStr(tmp);
    }
    return new Base64().encode(final)
}

function dec(jsText, cipherTxt) {
    jsText = jsText.replace(/TypeError\(.*?\)/g, "\"error\"");
    var pos = jsText.indexOf("TENCENT_CHAOS_VM");
    var PC = (pos += 17, jsText.slice(pos, pos + 1));
    var PB = (pos += 2, jsText.slice(pos, pos + 1));
    var STACK = (pos += 4, jsText.slice(pos, pos + 1));

    var HANDLE = /var [A-Za-z]=\[,*function/.exec(jsText)[0].slice(4, 5);
    var COD = /try\{for\(var [A-Za-z]=/.exec(jsText)[0].slice(12, 13);
    jsText = "var key;var flag=0;" + jsText.replace(COD + "=" + HANDLE + "[" + PB + "[" + PC + "++]]();", "{if(flag==1){return key;}" + COD + "=" + HANDLE + "[" + PB + "[" + PC + "++]]();" + "}").replace("R[R.length-2]=R[R.length-2]+R.pop()".replace(/R/g, STACK), 'if((R[R.length-2]==0x9E3779B9)||(R[R.length-1]==0x9E3779B9)){for(var i=0;i<R.length;i++){if(Array.isArray(R[i][0])&&R[i][0].length==4&&(typeof R[i][0][0])=="number"&&R[i][0][0]>1000){key=R[i][0];break;}};key.push(PB[PB.indexOf(0x9E3779B9) - 19]);key.push(PB[PB.indexOf(0x9E3779B9) - 53]);key.push(PB[PB.indexOf(0x9E3779B9) - 6]);key.push(PB[PB.indexOf(0x9E3779B9) + 15]);flag=1;return key;}R[R.length-2]=R[R.length-2]+R.pop()'.replace(/R/g, STACK).replace(/PB/g, PB));
    var tmpKey = dom.window.eval(jsText + "window.TDC.getData(!0)")
    return teaDecrypt(cipherTxt, tmpKey);
}
