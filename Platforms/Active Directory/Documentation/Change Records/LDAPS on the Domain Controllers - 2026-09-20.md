# LDAPS on the Domain Controllers

**Created:** 2026-09-20  
**Last updated:** 2026-09-20

LDAP over TLS never worked on this forest. Both controllers listened on 636 and reset every handshake, including handshakes from themselves. I found that while building directory sign-in for App Portal, which needs a bind that does not send a password in the clear, and fixed it by giving each controller a certificate it actually trusts.

## What was wrong

`Test-NetConnection -Port 636` succeeded on both controllers, which is why nothing had ever flagged this: the port is open because the service binds it either way. Every TLS handshake to it was reset immediately, from `docker-main`, from `HQ-DC01` to itself, and through both `openssl s_client` and .NET's `SslStream`.

The System log named the cause without ambiguity, six times over: Schannel event **36886**, *no suitable default server credential exists on this system*, whose own text says the directory server is the example of an application this breaks. The Directory Service log carried event 1220 to match.

Each controller did hold a certificate with a Server Authentication usage and a private key, created on 2026-09-12 for WinRM over HTTPS. Schannel would not use it as the default server credential because it is self-signed and the machine did not trust it. WinRM was unaffected because WinRM manages its own credential, which is exactly the distinction event 36886 draws.

## What I changed

On each controller, running as `SYSTEM` through the Proxmox guest agent because an SSH session has no network credential and `ldifde` answers *Inappropriate Authentication* there:

1. Created a local issuing certificate authority in the machine's Personal store, `CN=AlphaSec LDAPS Root HQ-DC01` and `CN=AlphaSec LDAPS Root HQ-DC02`, RSA 2048, SHA-256, ten years, `CA=true` with a path length of zero.
2. Issued an LDAPS certificate from it for the controller, three years, subject and subject alternative names covering the fully qualified and short host names, Server Authentication only.
3. Added the issuing authority, and only the authority, to the machine's Trusted Root store.
4. Restarted `NTDS` on the controller.

Each controller signs its own certificate with its own authority, and neither private key leaves the machine that made it. Two roots rather than one is the price of not carrying a CA key between hosts.

A leaf certificate trusted directly as a root would have satisfied Schannel (I tried that first and the handshake started working), but it fails for a client using GnuTLS, which will not accept a trust anchor without `CA=true`. OpenLDAP on Debian and Ubuntu is built against GnuTLS, so the portal could not have verified it. Issuing from a real authority satisfies both.

## Verification

| Check | Observed result |
|---|---|
| Handshake to `HQ-DC01` before the change | Reset by peer, from the controller itself and from `docker-main` |
| Schannel log before the change | Event 36886 on both controllers, event 1220 in Directory Service |
| Handshake to `HQ-DC01` after the change | TLS 1.3, subject `CN=hq-dc01.ad.alphasecunited.com`, issued by its authority |
| Handshake to `HQ-DC02` after the change | TLS 1.3, subject `CN=hq-dc02.ad.alphasecunited.com`, issued by its authority |
| Anonymous rootDSE read over LDAPS from a container on `docker-main` | `result: 0 Success` |
| Authenticated simple bind over LDAPS | A domain account bound and its group membership was read; see the [App Portal record](../../../App%20Portal/Documentation/Change%20Records/Directory%20Sign-In%20for%20the%20Portal%20-%202026-09-20.md) |
| Plain LDAP on 389 from `docker-main` | Still refused; only 636 was opened |

The certificate thumbprints are not published. They are pinned in the App Portal deployment's environment file on `docker-main`, and the two authority certificates are mounted there as a PEM bundle.

## Open

- These are private authorities on the controllers themselves, not AD CS. A real certificate services deployment would issue controller certificates automatically and renew them; this does not. The LDAPS certificates expire 2027-09-20 and the authorities 2036-09-20.
- Nothing else in the forest uses LDAPS yet. The only client is App Portal.
- The 2026-09-12 WinRM certificates are untouched and still self-signed; Windows Admin Center and WinRM continue to use them.
