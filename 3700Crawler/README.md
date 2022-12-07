# Web Crawler

The web crawler moves around `https://<server>:<port>/fakebook` and looks for secret flags.

The steps taken are as follows. The crawler:

1. Logs into the appropriate user at: `https://<server>:<port>/accounts/login/?next=/fakebook/`
2. Identifies secret flags in the HTML that follow the form: 
`<h3 class='secret_flag' style="color:red">FLAG: 64-characters-of-random-alphanumerics</h3>`
3. Parses other URL's in the webpage, identifies the ones that it has not accessed that are within the 
accepted domain, and navigates to those
4. Repeats steps 2 and 3 until all 5 flags have been found


### POST Request Headers

```http request
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
Accept-Encoding: gzip, deflate, br
Accept-Language: en-US,en;q=0.9
Cache-Control: max-age=0
Connection: keep-alive
Content-Length: 131
Content-Type: application/x-www-form-urlencoded
Cookie: csrftoken=mNBvpPHRy73Htmgs33zQv42d6gNa97ZI0ynggpm5n9SFB0slTeZ7RbQ0Nb70mBxD
Host: project5.3700.network
Origin: https://project5.3700.network
Referer: https://project5.3700.network/accounts/login/
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: same-origin
Sec-Fetch-User: ?1
Sec-GPC: 1
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.


request URL: https://project5.3700.network/accounts/login/
Request Method: POST
Status Code: 302 Found
Remote Address: 3.217.108.206:443
Referrer Policy: same-origin
```

### Post Content
```http request
username: ritzenhoff.j
password: 001286664
csrfmiddlewaretoken: FGnLL5hupsJMJn9VZpdIodCLSCCzje7bwFBJJTCHDUlJsCGhyfAfolfO9tL8FVY3
next: 
```

### Alternative POST Response

```http request
Cache-Control: max-age=0, no-cache, no-store, must-revalidate, private
Connection: keep-alive
Content-Language: en-us
Content-Length: 0
Content-Type: text/html; charset=utf-8
Cross-Origin-Opener-Policy: same-origin
Date: Thu, 07 Apr 2022 22:46:52 GMT
Expires: Thu, 07 Apr 2022 22:46:52 GMT
Location: /
Referrer-Policy: same-origin
Server: nginx
Set-Cookie: csrftoken=WGxgAOqMDP2C6rc9NirB1fZiz3R718gOUKZFi8PUn9MrsaeBxvWzNXwsGvDH4slv; expires=Thu, 06 Apr 2023 22:46:52 GMT; Max-Age=31449600; Path=/; SameSite=Lax
Set-Cookie: sessionid=hvxjh52m98ya6v8412a2hdwgjefyhfnk; expires=Thu, 21 Apr 2022 22:46:52 GMT; HttpOnly; Max-Age=1209600; Path=/; SameSite=Lax
Vary: Cookie, Accept-Language
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
```

### Following GET
```http request
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
Accept-Encoding: gzip, deflate, br
Accept-Language: en-US,en;q=0.9
Connection: keep-alive
Cookie: csrftoken=dBULDjuxYzLRJjpg6hQCzeIonGiOiWLW4A8JB7PKc1nOsyWCF7d9zmlrExrnEDCO; sessionid=9yp50p6mo9o7nd3yi3sz2ytivtns10fi
Host: project5.3700.network
Referer: https://project5.3700.network/
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: same-origin
Sec-Fetch-User: ?1
Sec-GPC: 1
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36
```


### Helpful Submission Commands
`zip -r p5.zip 3700crawler Makefile README.md networks lxml -x **/__pycache__`