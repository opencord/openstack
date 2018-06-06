# OpenStack Service #

## Purpose ##

The OpenStack Service is responsible for instantiating OpenStack Networks and Compute resources. Compute resources are referred to as "Servers" in the OpenStack API. This documentation may refer to "Servers" and "VMs" interchangeably.

## Transition from old to new OpenStack modeling ##

The OpenStack service is currently undergoing a transition from older modeling to newer modeling. The new models are currently in alpha status, and may have limited features and functionality. As work continues, it will soon be encouraged for new services to use the new models, which are described in this document.

The new models are primarily comprised of `TrustDomain`, `Principal`, `OpenStackService`, and `OpenStackServiceInstance`.

Some older models such as `Controller` and `Instance` may be removed at a future date.

Several models such as `Network`, `Image`, and `Flavor` are useful with both the older OpenStack modeling and the newer OpenStack modeling.

## Models ##

The following models are supported by the OpenStack Service:

- `OpenStackService`. Include parameters that are necessary for contacting a deployment of OpenStack.
    - `auth_url`. URL of the keystone endpoint.
    - `admin_user`. Username of the administrator.
    - `admin_password`. Password of the administrator.
    - `admin_tenant`. Project within which the administrator account resides.
- `TrustDomain`. Trust domains logically group services and their resources together into a namespace where the resources can be found. A TrustDomain corresponds to a OpenStack `domain`.
    - `name`. Name of the trust domain
    - `owner`. The service that is partitioned by this trust domain. For OpenStack trust domains, this will be an instance of the `OpenStackService` model.
- ```Principal```. Principals are entities that are able to perform operations on resources. A Principal corresponds to a OpenStack `User`.
    - `name`. Name of this principal.
    - `trust_domain`. TrustDomain in which this principal resides.
- `Flavor`. Represents the class of resources that will be used to instantiate a server. Corresponds directly to an OpenStack flavor.
    - `name`. Name of the flavor.
- `Image`. Images are virtual machine images that are used when instantiating servers.
    - `name`. Name of the image.
    - `container_format`. Format of the container. Usually set to `BARE`.
    - `disk_format`. Format of the disk image. Usually set to `QCOW2`.
    - `path`. URL where the image may be downloaded from.
- `Slice`. A Slice is a collection of compute resources and can also be thought of as a controller for those compute resources, implementing logic that creates and destroys the compute resources as necessary. For OpenStack-based slices, this logic is usually located in XOS model_policies.
    - `name`. Name of this Slice.
    - `site`. Site that this Slice belongs to, used for administrative accountability.
    - `trust_domain`. TrustDomain in which this slice resides.
- `NetworkTemplate`. Holds parameters that may be used for various classes of networks.
    - `name`. Name of network template.
    - `description`. Description of network template.
    - `visibility`. Whether or not the network is reachable externally. Set to `private` or `public`.
    - `translation`. Whether or not NATing is performed. Usually set to `none`.
    - `vtn_kind`. Passed to VTN to indicate the type of network. Choices are `PRIVATE`, `PUBLIC`, `MANAGEMENT_LOCAL`, `MANAGEMENT_HOST`, and `VSG`. Please see the VTN documentation for further details.
- `Network`. Represents a network that may be used to connect servers to each other and/or externally.
    - `name`. Name of network.
    - `owner`. Relation to the `Slice` object that owns this network.
    - `template`. Relation to a `NetworkTemplate` object.
    - `subnet`. Subnet, specified in CIDR notation. For example, `115.0.0.0/24`.
    - `permit_all_slices`. Set to True to permit all slices to connect to this network.
- `NetworkSlice`. This model is used to connect a Slice to a Network.
    - `network`. Relation to the Network to be connected.
    - `slice`. Relation to the Slice to be connected.
- `Node`. Used to represent an OpenStack compute node.
    - `name`. Hostname of node.
- `OpenStackServiceInstance`. This model directly represents an OpenStack Server, implemented as a virtual machine.
    - `name`. Name of the server.
    - `owner`. Service that owns this `ServiceInstance`, in this case, an instance of the `OpenStackService` model.
    - `slice`. Relation to the `Slice` that manages this server.
    - `image`. Relation to the `Image` that is used by this server.
    - `flavor`. Relation to the `Flavor` that should be used when instantiating this server.
    - `node`. Relation to the `Node` that this server should be instantiated on.

## Network Connectivity ##

Network connectivity is typically achieved by attaching `Networks` to `Slices`. Whenever an `OpenStackServiceInstance` is instantiated, the Server created in OpenStack will inherit all Networks connected (via `NetworkSlice` relations) to the `Slice` that owns the `OpenStackServiceInstance`.

A typical workflow for establishing network connectivity is:

1. Create a `Slice`
2. Create a `NetworkSlice` for each `Network` that should be attached to the `Slice`.
3. Create one or more `OpenStackServiceInstance` owned by the `Slice`.

## Creating OpenStack Objects in XOS ##

An XOS Service can leverage the OpenStack Service to creates OpenStack resources on behalf of the XOS Service. To create an OpenStack Server, it's suggested you create the following XOS Objects:

- `TrustDomain`
- `Principal`
- `Slice`
- `Image`
- `OpenStackServiceInstance`

It's often the case with most profiles, such as the `base-openstack` profile, that several object will automatically be created for you:

- `Site`. Usually that's one site named "mysite".
- `Flavor`. Often there are a variety of flavors, "m1.small", "m1.medium", "m1.large", etc.
- `Node`. Most profiles will create at least one usable compute node.

Below is a short example that will create an OpenStack server. This example uses the XOS python API and may be entered directly into `xossh`:

```python
# Create a new Trust Domain
t=TrustDomain(owner=OpenStackService.objects.first(), name="demo-trust")
t.save()

# Create a new Principal
p=Principal(trust_domain=t, name="demo-user")
p.save()

# Create a new Slice, attached to the first Site.
s=Slice(trust_domain=t, name="demo-slice", site=Site.objects.first())
s.save()

# Attach the Slice to the Management Network.
ns=NetworkSlice(slice=s, network=Network.objects.get(name="management"))
ns.save()

# Create an Image
img=Image(name="cirros-0.3.5", container_format="BARE", disk_format="QCOW2", path="http://download.cirros-cloud.net/0.3.5/cirros-0.3.5-x86_64-disk.img")
img.save()

# Use the first Node defined in XOS. Assumes node already exists.
node = Node.objects.first()

# Use the m1.medium flavor
flavor = Flavor.objects.get(name="m1.medium")

# Create the Server
i=OpenStackServiceInstance(slice=s, image=img, name="demo-instance", owner=OpenStackService.objects.first(), flavor=flavor, node=node)
i.save()
```
