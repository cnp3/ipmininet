from ipmininet.iptopo import IPTopo
from ipmininet.router.config import RouterConfig, BGP, ebgp_session, set_med, new_access_list, AF_INET6, \
    CLIENT_PROVIDER, SHARE


def error_msg(list_arg):
    """
    :param list_arg: list of strings
    :return: a string formed by all strings concatenated in a more readable way. All strings in list_arg are separated
            by ', '  except the last one, separated by ' or '
    """
    if len(list_arg) >= 1:
        msg = list_arg[0]
        if len(list_arg) > 1:
            for i in list_arg[1:]:
                if i == list_arg[-1]:
                    msg = msg + " or " + i
                    break
                msg = msg + ", " + i
        return msg
    return ''


def check_correct_link(link, as_list, link_type):
    """
    :param link: string given in input, should be either 'ok' or be in the format '[AS1] [AS2] [LINK]'
    :param as_list: list os AS
    :param link_type: list of type of link
    :return: a list and a boolean: (list with (2 valid AS, one valid link) and true) OR ([] and false)
    """
    if link == "ok":
        return [], False  # No link added
    else:
        link_details = link.split()
        if len(link_details) is not 3:
            raise IndexError("You did not enter the right number of words!\nPlease enter 3 words")
        if (link_details[0] not in as_list) or (link_details[1] not in as_list):
            raise ValueError(
                "You did not enter a valid AS!\nPlease enter distinct AS amongst %s\n" % (error_msg(as_list)))
        if link_details[0] == link_details[1]:
            raise ValueError("You entered two times the same AS!\nPlease enter distinct AS amongst %s\n" % (
                error_msg(as_list)))
        if link_details[2] not in link_type:
            raise ValueError(
                "You did not entered a valid type of link!\nPlease enter %s\n" % (error_msg(link_type)))
        return link_details, True  # Link format valid


class BGPAdjust(IPTopo):
    """This topology builds a 5-AS network exchanging BGP reachability as shown in the figure below
        Shared cost are described with ' = ', client - provider with ' $ '. The user can choose to add another link
        between 2 AS or to let the network as it is
    """

    def build(self, *args, **kwargs):
        """
            +-----+       +-----+
        +---+as4r |       |as3r +---+
        |   +--+--+       +--+--+   |
        |      |   \ =   / = | =    | =
        |      |    \   /    |      |
        |      |     \ /     |      |
        | $    | $    \      |      |
        |      |     / \     |      |
        |      |    /   \    |      |
        |      V   /     \   |      |
        |   +-----+       +--+--+   |
        |   |as2r |       |as5r |   |
        |   +--+--+       +-----+   |
        |      | =                  |
        |      |                    |
        |      |                    |
        |      |                    |
        |      |                    |
        |   +--+--+                 |
        +-->+as1r +-----------------+
            +-----+
        """

        list_as_name = ["as1r", "as2r", "as3r", "as4r", "as5r"]
        link_type_name = ["SHARE", "CLIENT_PROVIDER"]
        link_type_object = [SHARE, CLIENT_PROVIDER]
        expected_format = '[AS1] [AS2] [LINK]'

        link = input("Please enter the link you wish to add or 'ok' to let the network as it is\n"
                     "To add a link between 2 AS, type '" + expected_format + "' where\n"
                                                                              " - [AS1] is the first AS (e.g. 'as1r')\n"
                                                                              "- [AS2] is the second AS (e.g. "
                                                                              "'as2r')\n "
                                                                              " - [LINK] is the type of link, i.e.\n"
                                                                              "   * 'SHARE' for a shared-cost link\n"
                                                                              "   * 'CLIENT_PROVIDER' for a "
                                                                              "client-provider link\n")

        while True:
            try:
                l, change = check_correct_link(link, list_as_name, link_type_name)
                break
            except Exception as e:
                link = input("Error: {}\n Try again: '".format(str(e)) + expected_format + "'\n")

        # Add all routers
        as1r = self.addRouter('as1r')
        as2r = self.addRouter('as2r')
        as3r = self.addRouter('as3r')
        as4r = self.addRouter('as4r')
        as5r = self.addRouter('as5r')
        list_as_object = [as1r, as2r, as3r, as4r, as5r]
        as1r.addDaemon(BGP, address_families=(AF_INET6(networks=('2001:db:1::/48',)),))
        as2r.addDaemon(BGP, address_families=(AF_INET6(networks=('2001:db:2::/48',)),))
        as3r.addDaemon(BGP, address_families=(AF_INET6(networks=('2001:db:3::/48',)),))
        as4r.addDaemon(BGP, address_families=(AF_INET6(networks=('2001:db:4::/48',)),))
        as5r.addDaemon(BGP, address_families=(AF_INET6(networks=('2001:db:5::/48',)),))

        # Add links
        self.addLink(as1r, as2r)
        self.addLink(as1r, as3r)
        self.addLink(as1r, as4r)
        self.addLink(as2r, as3r)
        self.addLink(as2r, as4r)
        self.addLink(as3r, as5r)
        self.addLink(as4r, as5r)

        # Set AS-ownerships
        self.addAS(1, (as1r,))
        self.addAS(2, (as2r,))
        self.addAS(3, (as3r,))
        self.addAS(4, (as4r,))
        self.addAS(5, (as5r,))

        # Add BGP peering
        ebgp_session(self, as1r, as2r, SHARE)
        ebgp_session(self, as1r, as3r, SHARE)
        ebgp_session(self, as2r, as3r, SHARE)
        ebgp_session(self, as3r, as5r, SHARE)
        ebgp_session(self, as4r, as5r, SHARE)
        ebgp_session(self, as4r, as1r, CLIENT_PROVIDER)
        ebgp_session(self, as4r, as2r, CLIENT_PROVIDER)

        # Add custom link
        if change:
            src_as = None
            dst_as = None
            link_chosen = None
            for i in range(len(list_as_object)):
                if l[0] == list_as_name[i]:
                    src_as = list_as_object[i]
                    if dst_as is not None:
                        break
                if l[1] == list_as_name[i]:
                    dst_as = list_as_object[i]
                    if src_as is not None:
                        break
            for i in range(len(link_type_object)):
                if l[2] == link_type_name[i]:
                    link_chosen = link_type_object[i]
                    break
            self.addLink(src_as, dst_as)
            ebgp_session(self, src_as, dst_as, link_chosen)

        # Add test hosts
        for r in self.routers():
            self.addLink(r, self.addHost('h%s' % r))
        super(BGPAdjust, self).build(*args, **kwargs)
