load('.tanzu/tanzu_develop.py', 'tanzu_develop')
allow_k8s_contexts('eduk8s')

local_resource(
  'spring-petclinic-compile',
  './mvnw -Dmaven.test.skip=true -Dspring-boot.repackage.excludeDevtools=false package && ' + 
    'rm -rf target/jar-staging && ' +
    'unzip -o target/spring-petclinic-*.jar -d target/jar-staging && ' +
    'rsync --delete --inplace --checksum -r target/jar-staging/ .build',
  deps=['src', 'pom.xml'])

tanzu_develop(k8s_object="spring-petclinic",
              deps=['.build/'],
              resource_deps=['spring-petclinic-compile'],
              live_update=[
                sync('.build/BOOT-INF/lib', '/workspace/BOOT-INF/lib'),
                sync('.build/META-INF', '/workspace/META-INF'),
                sync('.build/BOOT-INF/classes', '/workspace/BOOT-INF/classes'),
              ])
