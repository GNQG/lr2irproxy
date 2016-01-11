lr2irproxy
======================
LR2IRに対するHTTP通信をいじったり監視したり乗っ取ったりできるHTTPサーバ+プロキシサーバ

動作要件
----------------
Python2.7.x (https://www.python.org/)

lxml (http://lxml.de/)

`127.0.0.1:80`で他のサーバ等を立てていないこと。

作者は Python2.7.9 + lxml3.5.0 on Win7HPx64 でのみ動作確認

使い方
----------------
lr2irproxy.pyが含まれるフォルダーをLR2beta3ディレクトリ直下に設置し、
lr2irproxy.pyを実行(ダブルクリック)する。

終了はCtrl+Cで行える。

ライバル内ランキング等についての注意
----------------
Webブラウザを経由する通信のみをいじりたいのであれば、たとえばWebブラウザの自動構成スクリプトを
```javascript
function FindProxyForURL(url, host){
  if (host == "www.dream-pro.info"){
    return "PROXY 127.0.0.1:80";
  else{
    return "DIRECT";
  }
} 
```
のように書けばlr2irproxyを使うようになる。

LR2body.exeの通信をlr2irproxyに渡すためにはwww.dream-pro.infoへの通信を127.0.0.1に渡す必要がある。

ひとつの方法として、hostsファイルに以下のエントリを加える方法がある。
```
127.0.0.1 www.dream-pro.info
```
自己責任でお願いします。

ライセンス
----------
* lr2irproxy

The MIT License (MIT)

Copyright (c) 2015 @GNQG

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

* lxml

Copyright (c) 2004 Infrae. All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

  1. Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.
   
  2. Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in
     the documentation and/or other materials provided with the
     distribution.

  3. Neither the name of Infrae nor the names of its contributors may
     be used to endorse or promote products derived from this software
     without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL INFRAE OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
