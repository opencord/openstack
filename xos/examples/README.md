The Cirros examples require use of a password to login. The default password is "cubswin:)"

The Ubuntu examples require use of an ssh key to login. Make sure to first set a public key for the
user account that you're going to use to create the instance. For most demos, this will likely be
the admin@opencord.org account. You can set the SSH key using the GUI, or you can set it by using
xossh:

```python
u=User.objects.first()
u.public_key = "the_contents_of_my_public_key"
u.save()
```
