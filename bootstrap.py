import os
import subprocess
import sys

CACERT = b'''\
-----BEGIN CERTIFICATE-----
MIIGWDCCBUCgAwIBAgIQCl8RTQNbF5EX0u/UA4w/OzANBgkqhkiG9w0BAQUFADBs
MQswCQYDVQQGEwJVUzEVMBMGA1UEChMMRGlnaUNlcnQgSW5jMRkwFwYDVQQLExB3
d3cuZGlnaWNlcnQuY29tMSswKQYDVQQDEyJEaWdpQ2VydCBIaWdoIEFzc3VyYW5j
ZSBFViBSb290IENBMB4XDTA4MDQwMjEyMDAwMFoXDTIyMDQwMzAwMDAwMFowZjEL
MAkGA1UEBhMCVVMxFTATBgNVBAoTDERpZ2lDZXJ0IEluYzEZMBcGA1UECxMQd3d3
LmRpZ2ljZXJ0LmNvbTElMCMGA1UEAxMcRGlnaUNlcnQgSGlnaCBBc3N1cmFuY2Ug
Q0EtMzCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAL9hCikQH17+NDdR
CPge+yLtYb4LDXBMUGMmdRW5QYiXtvCgFbsIYOBC6AUpEIc2iihlqO8xB3RtNpcv
KEZmBMcqeSZ6mdWOw21PoF6tvD2Rwll7XjZswFPPAAgyPhBkWBATaccM7pxCUQD5
BUTuJM56H+2MEb0SqPMV9Bx6MWkBG6fmXcCabH4JnudSREoQOiPkm7YDr6ictFuf
1EutkozOtREqqjcYjbTCuNhcBoz4/yO9NV7UfD5+gw6RlgWYw7If48hl66l7XaAs
zPw82W3tzPpLQ4zJ1LilYRyyQLYoEt+5+F/+07LJ7z20Hkt8HEyZNp496+ynaF4d
32duXvsCAwEAAaOCAvowggL2MA4GA1UdDwEB/wQEAwIBhjCCAcYGA1UdIASCAb0w
ggG5MIIBtQYLYIZIAYb9bAEDAAIwggGkMDoGCCsGAQUFBwIBFi5odHRwOi8vd3d3
LmRpZ2ljZXJ0LmNvbS9zc2wtY3BzLXJlcG9zaXRvcnkuaHRtMIIBZAYIKwYBBQUH
AgIwggFWHoIBUgBBAG4AeQAgAHUAcwBlACAAbwBmACAAdABoAGkAcwAgAEMAZQBy
AHQAaQBmAGkAYwBhAHQAZQAgAGMAbwBuAHMAdABpAHQAdQB0AGUAcwAgAGEAYwBj
AGUAcAB0AGEAbgBjAGUAIABvAGYAIAB0AGgAZQAgAEQAaQBnAGkAQwBlAHIAdAAg
AEMAUAAvAEMAUABTACAAYQBuAGQAIAB0AGgAZQAgAFIAZQBsAHkAaQBuAGcAIABQ
AGEAcgB0AHkAIABBAGcAcgBlAGUAbQBlAG4AdAAgAHcAaABpAGMAaAAgAGwAaQBt
AGkAdAAgAGwAaQBhAGIAaQBsAGkAdAB5ACAAYQBuAGQAIABhAHIAZQAgAGkAbgBj
AG8AcgBwAG8AcgBhAHQAZQBkACAAaABlAHIAZQBpAG4AIABiAHkAIAByAGUAZgBl
AHIAZQBuAGMAZQAuMBIGA1UdEwEB/wQIMAYBAf8CAQAwNAYIKwYBBQUHAQEEKDAm
MCQGCCsGAQUFBzABhhhodHRwOi8vb2NzcC5kaWdpY2VydC5jb20wgY8GA1UdHwSB
hzCBhDBAoD6gPIY6aHR0cDovL2NybDMuZGlnaWNlcnQuY29tL0RpZ2lDZXJ0SGln
aEFzc3VyYW5jZUVWUm9vdENBLmNybDBAoD6gPIY6aHR0cDovL2NybDQuZGlnaWNl
cnQuY29tL0RpZ2lDZXJ0SGlnaEFzc3VyYW5jZUVWUm9vdENBLmNybDAfBgNVHSME
GDAWgBSxPsNpA/i/RwHUmCYaCALvY2QrwzAdBgNVHQ4EFgQUUOpzidsp+xCPnuUB
INTeeZlIg/cwDQYJKoZIhvcNAQEFBQADggEBAB7ipUiebNtTOA/vphoqrOIDQ+2a
vD6OdRvw/S4iWawTwGHi5/rpmc2HCXVUKL9GYNy+USyS8xuRfDEIcOI3ucFbqL2j
CwD7GhX9A61YasXHJJlIR0YxHpLvtF9ONMeQvzHB+LGEhtCcAarfilYGzjrpDq6X
dF3XcZpCdF/ejUN83ulV7WkAywXgemFhM9EZTfkI7qA5xSU1tyvED7Ld8aW3DiTE
JiiNeXf1L/BXunwH1OH8zVowV36GEEfdMR/X/KLCvzB8XSSq6PmuX2p0ws5rs0bY
Ib4p1I5eFdZCSucyb6Sxa1GDWL4/bcf72gMhy2oWGU4K8K2Eyl2Us1p292E=
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
MIIDxTCCAq2gAwIBAgIQAqxcJmoLQJuPC3nyrkYldzANBgkqhkiG9w0BAQUFADBs
MQswCQYDVQQGEwJVUzEVMBMGA1UEChMMRGlnaUNlcnQgSW5jMRkwFwYDVQQLExB3
d3cuZGlnaWNlcnQuY29tMSswKQYDVQQDEyJEaWdpQ2VydCBIaWdoIEFzc3VyYW5j
ZSBFViBSb290IENBMB4XDTA2MTExMDAwMDAwMFoXDTMxMTExMDAwMDAwMFowbDEL
MAkGA1UEBhMCVVMxFTATBgNVBAoTDERpZ2lDZXJ0IEluYzEZMBcGA1UECxMQd3d3
LmRpZ2ljZXJ0LmNvbTErMCkGA1UEAxMiRGlnaUNlcnQgSGlnaCBBc3N1cmFuY2Ug
RVYgUm9vdCBDQTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAMbM5XPm
+9S75S0tMqbf5YE/yc0lSbZxKsPVlDRnogocsF9ppkCxxLeyj9CYpKlBWTrT3JTW
PNt0OKRKzE0lgvdKpVMSOO7zSW1xkX5jtqumX8OkhPhPYlG++MXs2ziS4wblCJEM
xChBVfvLWokVfnHoNb9Ncgk9vjo4UFt3MRuNs8ckRZqnrG0AFFoEt7oT61EKmEFB
Ik5lYYeBQVCmeVyJ3hlKV9Uu5l0cUyx+mM0aBhakaHPQNAQTXKFx01p8VdteZOE3
hzBWBOURtCmAEvF5OYiiAhF8J2a3iLd48soKqDirCmTCv2ZdlYTBoSUeh10aUAsg
EsxBu24LUTi4S8sCAwEAAaNjMGEwDgYDVR0PAQH/BAQDAgGGMA8GA1UdEwEB/wQF
MAMBAf8wHQYDVR0OBBYEFLE+w2kD+L9HAdSYJhoIAu9jZCvDMB8GA1UdIwQYMBaA
FLE+w2kD+L9HAdSYJhoIAu9jZCvDMA0GCSqGSIb3DQEBBQUAA4IBAQAcGgaX3Nec
nzyIZgYIVyHbIUf4KmeqvxgydkAQV8GK83rZEWWONfqe/EW1ntlMMUu4kehDLI6z
eM7b41N5cdblIZQB2lWHmiRk9opmzN6cN82oNLFpmyPInngiK3BD41VHMWEZ71jF
hS9OMPagMRYjyOfiZRYzy78aG6A9+MpeizGLYAiJLQwGXFK3xPkKmNEVX58Svnw2
Yzi9RKR/5CYrCsSXaQ3pjOLAEFe4yHYSkVXySGnYvCoCWw9E1CAx2/S6cCZdkGCe
vEsXCS+0yx5DaMkHJ8HSXPfqIbloEpw8nL+e/IBcm2PN7EeqJSdnoDfzAIJ9VNep
+OkuE6N36B9K
-----END CERTIFICATE-----
'''


def get_pip():
    # Download and execute the get-pip.py bootstrap script to install pip
    import shutil
    import tempfile
    from urllib.request import urlopen
    pip_url = 'https://raw.github.com/pypa/pip/master/contrib/get-pip.py'
    print('Downloading get-pip.py')
    tmpdir = tempfile.mkdtemp()
    try:
        cafile = os.path.join(tmpdir, 'cacert.pem')
        with open(cafile, 'wb') as file:
            file.write(CACERT)
        get_pip_py = os.path.join(tmpdir, 'get-pip.py')
        response = urlopen(pip_url, cafile=cafile)
        if response.status != 200:
            print('Server response:', response.status, response.reason,
                  file=sys.stderr)
            print('Error: Download failed!', file=sys.stderr)
            sys.exit(1)
        with open(get_pip_py, 'wb') as file:
            shutil.copyfileobj(response, file)
        print('Running get-pip.py')
        subprocess.check_call([sys.executable, get_pip_py])
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def stage1(directory='env', prompt='(openeis)'):
    import venv
    # Install the virtual environment.
    builder = venv.EnvBuilder(upgrade=os.path.exists(directory))
    # Override ensure_directories to set the prompt and get the context
    context = None
    _ensure_directories = builder.ensure_directories
    def ensure_directories(*args, **kwargs):
        nonlocal context
        context = _ensure_directories(*args, **kwargs)
        context.prompt = prompt
        return context
    builder.ensure_directories = ensure_directories
    builder.create(directory)
    # Call this script in the new virtual Python environment
    env = os.environ.copy()
    # Set the environment variable to keep Debian site.getsitepackages()
    # from appending 'local' to the prefix.
    env['VIRTUAL_ENV'] = context.env_dir
    subprocess.check_call([context.env_exe, __file__], env=env)


def stage2():
    try:
        import pip
    except ImportError:
        try:
            import ensurepip
        except ImportError:
            get_pip()
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-e', '.'])


def main(directory='env', prompt='(openeis)'):
    # venv and other features used in openeis were introduced in Python 3.3.
    if sys.version_info[:2] < (3, 3):
        sys.stderr.write('error: Python 3.3 or greater is required\n')
        sys.exit(1)
    if sys.base_prefix != sys.prefix:
        stage2()
    else:
        stage1()


if __name__ == "__main__":
    main()
