import re


def parse_dynamic_url(url):
    # Remove leading and trailing slashes for uniform processing
    leading_slash = url.startswith('/')
    trailing_slash = url.endswith('/')
    url = url.strip('/')

    # Compile the regex pattern outside the loop for efficiency
    pattern = re.compile(r"{(.*?)}")

    # Create the path with regex substitutions
    url_path = [
        pattern.sub(lambda m: f"(?P<{m.group(1)}>[^/]+?)", part)
        for part in url.split('/') if part
    ]

    # Join the parts back into a single path
    path = '/' + '/'.join(url_path) if leading_slash else '/'.join(url_path)
    if trailing_slash and not path.endswith('/'):
        path += '/'

    return path


match = re.match(r'^/users/(?P<id>[^/]+?)/$', "/users/123/")
match.groupdict()
url = parse_dynamic_url("/book/{name}/action/{author}")
# expression = r"\A%s\Z" % url
expression = r"^%s$" % url
teste = re.compile(expression, re.DOTALL)


aaaa = teste.match("/users/1234/")

print(aaaa.groupdict())


