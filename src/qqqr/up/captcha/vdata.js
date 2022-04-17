function Base64() {
    // private property
    this._keyStr = "GV5yc1_twaSpHPOE7R3jv9fqC2L-0TxMi4FuolBAbQeIgJU*XzZKWkDNh6n8dsrmY";
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
    input = input.replace(/[^A-Za-z0-9_\*\-]/g, "");
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

function EncryptBlock(EncryData) {
    var Key = [845493299, 812005475, 825582135, 1684093238];    // 34e2c8f07b5169ad
    var x = EncryData[0];
    var y = EncryData[1];
    var sum = 0;
    var delta = 0x9E3779B9;
    for (var i = 0; i < 32; i++) {
        x += (((y << 4) ^ (y >>> 5)) + y) ^ (sum + Key[sum & 3]);
        sum += delta;
        y += (((x << 4) ^ (x >>> 5)) + x) ^ (sum + Key[(sum >> 11) & 3]);
    }
    return [x, y];
}

function DecryptBlock(DecryData) {
    var Key = [845493299, 812005475, 825582135, 1684093238];
    var x = DecryData[0];
    var y = DecryData[1];
    var sum = 0x9E3779B9 * 32;
    var delta = 0x9E3779B9;
    for (var i = 0; i < 32; i++) {
        y -= (((x << 4) ^ (x >>> 5)) + x) ^ (sum + Key[(sum >> 11) & 3]);
        sum -= delta;
        x -= (((y << 4) ^ (y >>> 5)) + y) ^ (sum + Key[sum & 3]);
    }
    return [x, y];
}
var teaDecrypt = function (msg) {
    var res = new Base64().decode(msg);
    var rounds = res.length >> 3;
    var tmp;
    var final = "";
    for (var i = 0; i < rounds; i++) {
        tmp = DecryptBlock(strToLongs(res.slice(i * 8, i * 8 + 8)));
        final += longsToStr(tmp);
    }
    return final;
}

function teaEncrypt(msg) {
    var b64 = new Base64();
    var final = "";
    var rounds = msg.length >> 3;
    for (var i = 0; i < rounds; i++) {
        tmp = EncryptBlock(strToLongs(msg.slice(i * 8, i * 8 + 8)));
        final += longsToStr(tmp);
    }
    return b64.encode(final)
}

function seqEncode(msg) {
    var tmp = msg.length % 16;
    var ch = "0abcdefghijklmnop".charAt(tmp)
    while (tmp && (16 - tmp)) {
        msg += ch;
        tmp++;
    }
    var keyMap = [0, 4, 8, 12, 5, 9, 13, 1, 10, 14, 2, 6, 15, 3, 7, 11];
    tmp = msg.length >> 4;

    var res = "";
    for (var i = 0; i < tmp; i++) {
        var cut = msg.slice(i * 16, i * 16 + 16);
        for (var j = 0; j < 16; j++) {
            res += cut.charAt(keyMap[j])
        }
    }
    return res;
}
function seqDecode(msg) {
    var keyMap = [0, 7, 10, 13, 1, 4, 11, 14, 2, 5, 8, 15, 3, 6, 9, 12];
    var tmp = msg.length >> 4;
    var res = "";
    for (var i = 0; i < tmp; i++) {
        var cut = msg.slice(i * 16, i * 16 + 16);
        for (var j = 0; j < 16; j++) {

            res += cut.charAt(keyMap[j])
        }
    }
    return res;
}

function enc(params) {
    return teaEncrypt(seqEncode(params))
}

function dec(vdata) {
    return seqDecode(teaEncrypt(vdata))
}
