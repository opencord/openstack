# xosproject/neutron-onos image

The file `neutron-newton-plus-onos-ml2` is used to generate the
[xosproject/neutron-onos](https://hub.docker.com/r/xosproject/neutron-onos)
container which includes the ONOS plugin for Neutron, which is used with
[openstack-helm](https://guide.opencord.org/prereqs/openstack-helm.html).

## Build instructions

```shell
docker build -t xosproject/neutron-onos -f neutron-newton-plus-onos-ml2 .
```

