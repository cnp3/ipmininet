from ipmininet.iptopo import IPTopo
from ipmininet.router.config import RouterConfig, BGP, ebgp_session, set_local_pref, new_access_list



class BGPTopoLocalPref(IPTopo):
	"""This topology is composed of two AS connected in dual homing with different local pref"""

	def build(self, *args, **kwargs):
		"""
	TODO
           +----------+                                   +--------+
                      |                                   |
         AS1          |                  AS2              |        AS3
                      |                                   |
                      |                                   |
    +-------+   eBGP  |  +-------+     iBGP    +-------+  |  eBGP   +-------+
    | as1r1 +------------+ as2r1 +-------------+ as2r2 +------------+ as3r1 |
    +-------+         |  +-------+             +-------+  |         +-------+
                      |                                   |
                      |                                   |
                      |                                   |
         +------------+                                   +--------+
        """
		# Add all routers
		as1r1 = self.addRouter('as1r1')
		as1r1.addDaemon(BGP)
		as1r2 = self.addRouter('as1r2')
		as1r2.addDaemon(BGP)
		as1r3 = self.addRouter('as1r3')
		as1r3.addDaemon(BGP)
		as1r4 = self.addRouter('as1r4')
		as1r4.addDaemon(BGP)
		as1r5 = self.addRouter('as1r5')
		as1r5.addDaemon(BGP)
		as1r6 = self.addRouter('as1r6')
		as1r6.addDaemon(BGP)
		as4r1 = self.addRouter('as4r1')
		as4r1.addDaemon(BGP, address_families=(_bgp.AF_INET6(networks=('dead:beef::/32',)),))
		as4r2 = self.addRouter('as4r2')
		as4r2.addDaemon(BGP, address_families=(_bgp.AF_INET6(networks=('dead:beef::/32',)),))
		h1 = self.addHost("h1")
        h2 = self.addHost("h2")

		# Add Links
		self.addLink(as1r1, as1r6, params1={"ip": ("fd00:1:1::1/48",)},
                     params2={"ip": ("fd00:1:1::2/48",)})
		self.addLink(as1r1, as1r3, params1={"ip": ("fd00:1:2::1/48",)},
                     params2={"ip": ("fd00:1:2::2/48",)})
		self.addLink(as1r3, as1r2, params1={"ip": ("fd00:3:1::1/48",)},
                     params2={"ip": ("fd00:3:1::2/48",)})
		self.addLink(as1r3, as1r6, params1={"ip": ("fd00:3:2::1/48",)},
                     params2={"ip": ("fd00:3:2::2/48",)})
		self.addLink(as1r2, as1r4, params1={"ip": ("fd00:4:1::1/48",)},
                     params2={"ip": ("fd00:4:1::2/48",)})
		self.addLink(as1r4, as1r5, params1={"ip": ("fd00:4:2::1/48",)},
                     params2={"ip": ("fd00:4:2::2/48",)})
		self.addLink(as1r5, as1r6, params1={"ip": ("fd00:5:1::1/48",)},
                     params2={"ip": ("fd00:5:1::2/48",)})
		self.addLink(as4r1, as1r6; params1={"ip": ("fd00:6:1::1/48",)},
                     params2={"ip": ("fd00:6:1::2/48",)})
		self.addLink(as4r2, as1r5, params1={"ip": ("fd00:5:2::1/48",)},
                     params2={"ip": ("fd00:5:2::2/48",)})
		self.addLink(as4r1, h1, params1={"ip": ("dead:beef::1/32",)},
                     params2={"ip": ("dead:beef::2/32",)})
		self.addLink(as4r2, h2, params1={"ip": ("dead:beef::1/32",)},
                     params2={"ip": ("dead:beef::2/32",)})


		new_access_list(self, (as1r6, as1r5, as2r1, as2r2), 'all', ('any',))
		set_local_pref(self, as1r6, as4r1, 99, filter_type='access-list', filter_names=('all',))
		set_local_pref(self, as1r5, as4r2, 50, filter_type='access-list', filter_names=('all',))


		# Add full mesh
		self.addAS(4, (as4r1, as4r2))
		self.addiBGPFullMesh(1, (as1r1, as1r2, as1r3, as1r4, as1r5, as1r6))

		# Add eBGP session
		ebgp_session(self, as1r6, as4r1)
		ebgp_session(self, as1r5, as4r2)

		# Add test hosts ?
		# for r in self.routers():
		#     self.addLink(r, self.addHost('h%s' % r))
		super(BGPTopoLocalPref, self).build(*args, **kwargs)

	def bgp(self, name):
		r = self.addRouter(name, config=RouterConfig)
		r.addDaemon(BGP, address_families=(
			_bgp.AF_INET(redistribute=('connected',)),
			_bgp.AF_INET6(redistribute=('connected',))))
		return r
