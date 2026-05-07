def generate_affiliate_link(url):
    ref_tag = "ref=mydealsapp"
    if "?" in url:
        return f"{url}&{ref_tag}"
    else:
        return f"{url}?{ref_tag}"
