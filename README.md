# Alexa Check

## Introduction

The **Alexa Top Websites** (https://www.alexa.com/topsites) are used to monitor the popularity trend of a website and compare the popularity of different websites.

In order to gauge the security posture of the internet as a whole collecting information from the Alexa Top Sites is useful. **AlexaCheck.py** assists by building a PostgreSQL database that stores header information from each website, the first listed resolved IP address, HTTP response code, and MX records.  The header information also includes cookies that are passed during an initial connection. This approach was used to examine security of the **Alexa Top Websites** in a research paper **CookiExt: Patching the Browser Against Session Hijacking Attacks**.

**AlexaCheck.py** can also accept a list of other domains you want to check for forced TLS encryption and inspect cookies and other header information as part of the reconnaissance scope of a penetration test.

## Specific HTTP Security Risks

### SSL/TLS Enforcement

The **Alexa Check** database allows analysis of a particular website for security.  For example if a site does not enforce encryption for user connections.  This can be identified by a site returning a **200 OK** response code for an insecure connection such as **http://domain.com** reveals that the site does not strictly force transport layer security (SSL/TLS).  This means the site is susceptible to a **MiTM (man in the middle)** attack.  If these sites offer user accounts and use the PHP session cookies as its only means to maintain state of the user's device a session hijacking attack is possible.

Mitigating **MiTM** attacks can be done by forwarding any requests for **http://** to **https://** port 443.  Of course you must have a certificate for your domain issued by a certificate authority but those are available for free from The Electronic Frontier Foundation's (EFF) Let's Encrypt (https://letsencrypt.org/), which can be installed easily using **certbot**, and set to automatically renew with a cron.  In fact, using certbot will also automatically configure the webserver to forward **http://** traffic to **https://**, although you will also want to **forward any requests for the raw IP address itself to the domain**.

#### Create TLS Certificate Linux Apache Servers with Let's Encrypt Certbot:

    # Install required SSL packages
    $ yum install -y mod_ssl python-certbot-apache
    # Registering a SSL certificate with Let's Encrypt
    $ certbot --non-interactive --agree-tos --redirect --hsts --uir -m <your@emailaddress.com> --apache -d <site-domain> -d www.<site-domain>
    # Adding a crontab schedule to renew SSL certificates
    $ crontab -l | { cat; echo "30 2 * * * /usr/bin/certbot renew >> /var/log/le-renew.log"; } | crontab -

### Other Security Headers

The headers of a website can also provide other security related information such as **X-Frame-Options** settings, **HTTP-Only** and **Secure** cookie flags, **x-xss-protection** setting, and more. **HTTP-Only** and **Secure** cookie flags determine whether cookies are passed over insecure http connections and whether those cookies are available via JavaScript.  By configuring a web server to restrict cookies from being read in JavaScript, a website can protect users from having their cookies read by a browser plugin, or by an Cross Site Scripting (XSS) attack.  **x-xss-protection** header is a feature of Internet Explorer, Chrome and Safari that gives the user's browser explicit instructions to now allow <script> tags in any of its URLS.  This adds some protection to XSS attacks that target the URL, mitigating any inability to handle XSS on the server side.  There are even more security headers, and if you want to know more I suggest checking out **Scott Helme's** informative website (https://scotthelme.co.uk) because he seems to be the most knowledgable person on the internet regarding security headers.

#### Example of a HTTP Header with Some Security Headers Set

    $ curl -I https://www.google.com
    HTTP/2 200
    content-type: text/html; charset=ISO-8859-1
    p3p: CP="This is not a P3P policy! See g.co/p3phelp for more info."
    date: Thu, 13 May 2021 23:48:12 GMT
    server: gws
    x-xss-protection: 0
    x-frame-options: SAMEORIGIN
    expires: Thu, 13 May 2021 23:48:12 GMT
    cache-control: private
    set-cookie: 1P_JAR=2021-05-13-23; expires=Sat, 12-Jun-2021 23:48:12 GMT; path=/; domain=.google.com; Secure
    set-cookie: NID=215=GRtLi_uc0VMP7gUNDOpZJ6F_45N5iia4_CQUZJ-39YSAK7bBVgYU2g-a9Y0Z_UVeJhqHUHdfKqQqsrxutjwhxMdg9xws6i2d6TLH0dbsXsc1iUUKHrPYxhf5PK66KY_t6N6cV5Vfbl9S-AqDqpIOZLe2yvG4hdf70PonocviYOk; expires=Fri, 12-Nov-2021 23:48:12 GMT; path=/; domain=.google.com; HttpOnly
    alt-svc: h3-29=":443"; ma=2592000,h3-T051=":443"; ma=2592000,h3-Q050=":443"; ma=2592000,h3-Q046=":443"; ma=2592000,h3-Q043=":443"; ma=2592000,quic=":443"; ma=2592000; v="46,43"

**References**

[1] The HTTPS-Only Standard
https://https.cio.gov/

[2] How widely used are security based HTTP response headers?
https://scotthelme.co.uk/how-widely-used-are-security-based-http-response-headers/

[3] Hardening your HTTP response headers
https://scotthelme.co.uk/hardening-your-http-response-headers/

[4] Want to Encrypt All The Things? Firefox has you covered with HTTPS-Only Mode!
https://scotthelme.co.uk/tag/https-only-mode/

[5] Security Headers Updates
https://scotthelme.co.uk/security-headers-updates/

[6] CookiExt: Patching the Browser Against Session Hijacking Attacks, Journal of Computer Security (2015)
