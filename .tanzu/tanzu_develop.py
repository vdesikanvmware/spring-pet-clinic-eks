load('ext://local_output', 'local_output')
load('ext://file_sync_only', 'file_sync_only')
# -*- mode: Python -*-

# live reload
def tanzu_develop(k8s_object, deps=["."], resource_deps=[], live_update=[]):

    # 1. Create a CRD that we can create instances of that act as Tilt's image target
    twp_crd = """
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: tiltworkloadproxys.experimental.desktop.local
spec:
  group: experimental.desktop.local
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                image:
                  type: string
  scope: Namespaced
  names:
    plural: tiltworkloadproxys
    singular: tiltworkloadproxy
    kind: TiltWorkloadProxy
    shortNames:
    - twp
"""
    local("cat << EOF | kubectl apply -f - " + twp_crd + "EOF")
    
    # 2. Tell Tilt about it, so Tilt knows which container to update
    k8s_kind('TiltWorkloadProxy', api_version='experimental.desktop.local/v1',
            image_json_path="{.spec.image}")

    # 3. Fetch the image from the cluster
    ksvc_image_json_path = '{.spec.template.spec.containers[0].image}'
    ksvc_image = local_output('kubectl get ksvc ' + k8s_object + ' -o jsonpath=\'' + ksvc_image_json_path + '\'')
    ksvc_image = ksvc_image.replace('@sha256', '') # 3rd party `file_sync_only` wants image-name:actualsha not image-name@sha256:actualsha

    # 4. Create an instance of the tilt workload proxy to represent the app
    twp_template = """
apiVersion: "experimental.desktop.local/v1"
kind: TiltWorkloadProxy
metadata:
  name: {k8s_object}-twp
spec:
  image: {image}    
"""
    twp = twp_template.format(k8s_object=k8s_object, image=ksvc_image)
    local("cat << EOF | kubectl apply -f - " + twp + "EOF")

    k8s_resource(k8s_object+'-twp', port_forwards=["8080:8080", "9005:9005"],
                resource_deps=resource_deps,
                extra_pod_selectors=[{'serving.knative.dev/service' : k8s_object}])

    # 5. Wire-up Tilt's live updates to the pod
    file_sync_only(image=ksvc_image,
                   manifests=[blob(twp)],
                   deps=deps,
                   live_update=live_update)
 
