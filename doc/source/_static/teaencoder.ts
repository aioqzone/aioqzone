// https://cdnjs.cloudflare.com/ajax/libs/crypto-js/4.2.0/crypto-js.min.js
// https://cdnjs.cloudflare.com/ajax/libs/jsencrypt/3.3.2/jsencrypt.min.js

const base64 = CryptoJS.enc.Base64;
const hex = CryptoJS.enc.Hex;
const utf8 = CryptoJS.enc.Utf8;

const delta = 0x9E3779B9;
const PUBKEY = {
    e: 29496410687140474961119245498915887699746044446431573370755803330798106970246404153324791276945613538908384803873682125117660027361723341249004819631069444529772469791984089750098105980017598210197651262912913003686191561807018747713133181122140185218267859189424249203315474970083525464658420601178962825467757646812713543951322998963854566864529737741968186080598661524321050149157809052160123823325600419947995213991733248714968482744503612161143440082407680406893798778565223892792085769105886059245894371386120558683710768503711260651478376959795916731934526910610532162307615665046831918144682579200585877303789n,
    n: 65537,
}

function TeaEncoder(passwd: string) {
    this._passwd = passwd;

    function hexlify(data: Iterable<number>) {
        return new Uint8Array(utf8.parse(hex.stringify(data)));
    }

    function buffer_add(...buffer: ArrayLike<number>[]) {
        for (var sum = 0, i = 0; i < buffer.length; i++) sum += buffer[i].length;
        var r = new Uint8Array(sum);
        for (sum = 0, i = 0; i < buffer.length; i++) r.set(buffer[i], sum);
        return r;
    }

    function _xor(a: Uint32Array, b: Uint32Array, dst?: ArrayBuffer | undefined) {
        if (dst === undefined) dst = new ArrayBuffer(8);
        let dst_view = new Uint32Array(dst);
        for (let i = 0; i < 2; i++) dst_view[i] = a[i] ^ b[i];
        return dst;
    }

    function _tea(data: Uint32Array, key: Uint32Array) {
        const o = key[0], r = key[1], a = key[2], l = key[3];
        let s = 0, y = data[0], z = data[1];
        for (let i = 0; i < 16; i++) {
            s += delta;
            s &= 0xFFFFFFFF;
            y += ((z << 4) + o) ^ (z + s) ^ ((z >> 5) + r);
            y &= 0xFFFFFFFF;
            z += ((y << 4) + a) ^ (y + s) ^ ((y >> 5) + l);
            z &= 0xFFFFFFFF;
        }
        return new Uint32Array([y, z]);
    }

    function _hex2bytes(t: Uint8Array) {
        const s: string = utf8.stringify(t);
        var e = new Array<number>();
        for (let i = 0; i < s.length; i += 2)
            e.push(parseInt(s.slice(i, i + 2), 16));
        return new Uint8Array(e);
    }

    function tea_encrypt(data: Uint8Array, key: Uint8Array) {
        const data_view = _hex2bytes(data), key_view = new Uint32Array(hex.parse(key));

        let vl = data_view.length, filln = (vl + 10) % 8;
        if (filln > 0) filln = 8 - filln;

        var fills = [0xF8 & Math.floor(Math.random() * 0xFF) | filln];
        for (let i = 0; i < filln + 2; i++)
            fills.push(Math.floor(Math.random() * 0xFF));

        var all_data = new ArrayBuffer(fills.length + vl + 7),
            all_data_u1 = new Uint8Array(all_data),
            all_data_u4 = new Uint32Array(all_data);

        if (all_data_u1.length % 8 !== 0) {
            throw new Error('Data length must be a multiple of 8');
        }
        all_data_u1.set(fills);
        all_data_u1.set(data_view, fills.length);
        all_data_u1.set(Array(7).fill(0), fills.length + vl);


        var last_out = new ArrayBuffer(8),
            last_in = new ArrayBuffer(8),
            tmp = new ArrayBuffer(8);
        var last_out_u4 = new Uint32Array(last_out),
            last_out_u1 = new Uint8Array(last_out),
            last_in_u4 = new Uint32Array(last_in),
            tmp_u4 = new Uint32Array(tmp);
        var r = Array<number>();
        for (let i = 0; i < all_data_u4.length; i += 2) {
            _xor(all_data_u4.slice(i, i + 2), last_out_u4, tmp);
            _xor(_tea(tmp_u4, key_view), last_in_u4, last_out);
            last_in_u4.set(tmp_u4);
            r.push(...last_out_u1);
        }

        return hexlify(r);
    }

    function _upper_md5(raw_str: string) {
        let hex_str: string = CryptoJS.MD5(raw_str).toString();
        return new Uint8Array(utf8.parse(hex_str.toUpperCase()));
    }

    function _int2hex(ct: number) {
        return new Uint8Array(utf8.parse(hex.stringify([ct])));
    }

    function _rsa_encrypt(data: Uint8Array) {
        var encrypt = new JSEncrypt();
        encrypt.setPublicKey(PUBKEY);
        var encrypted: string = encrypt.encrypt(utf8.stringify(data));
        return hexlify(new Uint8Array(utf8.parse(encrypted)));
    }

    function get_encryption(salt: string, verifycode: string, is_safe: boolean = false) {
        if (this._passwd.length < 8) {
            throw "password.length in [8, 16]";
        }
        // verifycode先转换为大写，然后转换为bytes
        const vcode = hexlify(utf8.parse(verifycode.toUpperCase()));
        // verifycode length
        var vcode_len = _int2hex(vcode.length / 2);
        vcode_len = buffer_add(new Uint8Array(4 - vcode_len.length), vcode_len);
        const passwd = is_safe ? new Uint8Array(utf8.parse(this._passwd.toUpperCase())) : _upper_md5(this._passwd);
        const raw_salt = new TextEncoder().encode(salt);

        var p = buffer_add(_hex2bytes(passwd), raw_salt);
        p = _upper_md5(utf8.stringify(p));

        let enc = buffer_add(passwd, hexlify(raw_salt), vcode_len, vcode);
        enc = tea_encrypt(enc, p);

        let enc_len = _int2hex(enc.length / 2)
        enc_len = buffer_add(new Uint8Array(4 - enc_len.length), enc_len);
        enc = _rsa_encrypt(_hex2bytes(buffer_add(enc_len, enc)));

        return base64.stringify(enc).replace(/[\/\+=]/g, (t: string) => {
            return {
                "/": "-",
                "+": "*",
                "=": "_"
            }[t];
        });
    }

    this.encode = get_encryption;
}
