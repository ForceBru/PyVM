// Original: https://stackoverflow.com/a/27639437/4354477

#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <sys/utsname.h>

int main(void) {

   struct utsname buffer;

   errno = 0;
   if (uname(&buffer) != 0) {
      perror("uname");
      exit(EXIT_FAILURE);
   }

   printf("system name = '%s'\n", buffer.sysname);
   printf("node name   = '%s'\n", buffer.nodename);
   printf("release     = '%s'\n", buffer.release);
   printf("version     = '%s'\n", buffer.version);
   printf("machine     = '%s'\n", buffer.machine);

   #ifdef _GNU_SOURCE
      printf("domain name = %s\n", buffer.domainname);
   #endif

   return EXIT_SUCCESS;
}
