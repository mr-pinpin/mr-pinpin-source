/* Native Atlas pilot. Owned functional code: MIT; illustrations retain CONTENT-LICENSE.md. */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <unistd.h>
#include <limits.h>
/* SDL2's stable public ABI. No SDL_SysWMinfo or private LG structure is used. */
typedef struct SDL_Window SDL_Window;
extern int SDL_Init(uint32_t), SDL_PollEvent(void *), SDL_GL_SetAttribute(int,int), SDL_GL_SetSwapInterval(int);
extern int SDL_SetHint(const char *,const char *);
extern SDL_Window *SDL_CreateWindow(const char *,int,int,int,int,uint32_t);
extern void *SDL_GL_CreateContext(SDL_Window *);
extern void SDL_GL_SwapWindow(SDL_Window *), SDL_GL_DeleteContext(void *), SDL_DestroyWindow(SDL_Window *), SDL_Quit(void), SDL_Delay(uint32_t);
extern uint64_t SDL_GetPerformanceCounter(void), SDL_GetPerformanceFrequency(void);
extern const char *SDL_GetError(void);
/* GLES2 public ABI; the TV provides these functions through libGLESv2. */
typedef unsigned int GLuint, GLenum; typedef int GLint, GLsizei; typedef float GLfloat;
extern GLuint glCreateShader(GLenum),glCreateProgram(void);
extern void glShaderSource(GLuint,GLsizei,const char *const *,const GLint *),glCompileShader(GLuint),glGetShaderiv(GLuint,GLenum,GLint *),glGetShaderInfoLog(GLuint,GLsizei,GLsizei *,char *);
extern void glAttachShader(GLuint,GLuint),glLinkProgram(GLuint),glGetProgramiv(GLuint,GLenum,GLint *),glGetProgramInfoLog(GLuint,GLsizei,GLsizei *,char *),glUseProgram(GLuint);
extern GLint glGetAttribLocation(GLuint,const char *),glGetUniformLocation(GLuint,const char *);
extern void glUniform4f(GLint,GLfloat,GLfloat,GLfloat,GLfloat),glUniform1i(GLint,GLint),glGenBuffers(GLsizei,GLuint *),glBindBuffer(GLenum,GLuint),glBufferData(GLenum,long,const void *,GLenum);
extern void glEnableVertexAttribArray(GLuint),glVertexAttribPointer(GLuint,GLint,GLenum,unsigned char,GLsizei,const void *),glDrawArrays(GLenum,GLint,GLsizei);
extern void glGenTextures(GLsizei,GLuint *),glBindTexture(GLenum,GLuint),glTexParameteri(GLenum,GLenum,GLint),glTexImage2D(GLenum,GLint,GLint,GLsizei,GLsizei,GLint,GLenum,GLenum,const void *);
extern void glViewport(GLint,GLint,GLsizei,GLsizei),glClearColor(GLfloat,GLfloat,GLfloat,GLfloat),glClear(GLenum),glEnable(GLenum),glBlendFunc(GLenum,GLenum),glDeleteTextures(GLsizei,const GLuint *),glDeleteBuffers(GLsizei,const GLuint *),glDeleteProgram(GLuint),glDeleteShader(GLuint);
#define TEX 0x0DE1
#define ARRAY 0x8892
static GLuint program,vbo,white; static GLint attr,uvattr,tint;
static const float W=1920,H=1080;
static float clamp(float x,float a,float b){return fmaxf(a,fminf(b,x));}
static int event_int(const unsigned char *e,int offset){int v;memcpy(&v,e+offset,4);return v;}
static GLuint shader(GLenum type,const char *text){GLuint s=glCreateShader(type);GLint ok;glShaderSource(s,1,&text,NULL);glCompileShader(s);glGetShaderiv(s,0x8B81,&ok);if(!ok){char b[1024];glGetShaderInfoLog(s,sizeof b,NULL,b);fprintf(stderr,"shader: %s\n",b);exit(2);}return s;}
static GLuint texture(const char *path,int w,int h){size_t n=(size_t)w*h*4;unsigned char *p=malloc(n);FILE *f=fopen(path,"rb");if(!p||!f||fread(p,1,n,f)!=n){fprintf(stderr,"asset unavailable: %s\n",path);exit(3);}if(fgetc(f)!=EOF){fprintf(stderr,"asset size mismatch: %s\n",path);exit(3);}fclose(f);GLuint t;glGenTextures(1,&t);glBindTexture(TEX,t);glTexParameteri(TEX,0x2801,0x2601);glTexParameteri(TEX,0x2800,0x2601);glTexParameteri(TEX,0x2802,0x812F);glTexParameteri(TEX,0x2803,0x812F);glTexImage2D(TEX,0,0x1908,w,h,0,0x1908,0x1401,p);free(p);return t;}
static void quad(GLuint tex,float x,float y,float w,float h,float u,float v,float uw,float vh,float r,float g,float b,float a){float l=x/W*2-1,rr=(x+w)/W*2-1,top=1-y/H*2,bot=1-(y+h)/H*2;float z[]={l,top,u,v,rr,top,u+uw,v,l,bot,u,v+vh,rr,bot,u+uw,v+vh};glBindTexture(TEX,tex);glUniform4f(tint,r,g,b,a);glBindBuffer(ARRAY,vbo);glBufferData(ARRAY,sizeof z,z,0x88E0);glVertexAttribPointer((GLuint)attr,2,0x1406,0,4*sizeof(float),(void *)0);glVertexAttribPointer((GLuint)uvattr,2,0x1406,0,4*sizeof(float),(void *)(2*sizeof(float)));glDrawArrays(0x0005,0,4);}
int main(void){char executable[PATH_MAX];ssize_t n=readlink("/proc/self/exe",executable,sizeof executable-1);if(n>0){executable[n]=0;char *slash=strrchr(executable,'/');if(slash){*slash=0;if(chdir(executable)){perror("chdir");return 1;}}}
 setenv("SDL_WEBOS_ACCESS_POLICY_KEYS_BACK","true",1);SDL_SetHint("SDL_VIDEO_ALLOW_SCREENSAVER","0");
 if(SDL_Init(0x20)){fprintf(stderr,"SDL: %s\n",SDL_GetError());return 1;}
 SDL_GL_SetAttribute(21,4);SDL_GL_SetAttribute(17,2);SDL_GL_SetAttribute(18,0);SDL_GL_SetAttribute(0,8);SDL_GL_SetAttribute(1,8);SDL_GL_SetAttribute(2,8);SDL_GL_SetAttribute(3,8);SDL_GL_SetAttribute(6,0);SDL_GL_SetAttribute(7,0);SDL_GL_SetAttribute(5,1);
 SDL_Window *window=SDL_CreateWindow("family-native",0,0,(int)W,(int)H,0x2|0x4|0x10);if(!window){fprintf(stderr,"window: %s\n",SDL_GetError());return 1;}void *context=SDL_GL_CreateContext(window);if(!context){fprintf(stderr,"GL: %s\n",SDL_GetError());return 1;}SDL_GL_SetSwapInterval(1);
 const char *vs="attribute vec2 p;attribute vec2 uv;varying vec2 t;void main(){t=uv;gl_Position=vec4(p,0.,1.);}";
 const char *fs="precision mediump float;varying vec2 t;uniform sampler2D image;uniform vec4 color;void main(){gl_FragColor=texture2D(image,t)*color;}";
 GLuint vertex=shader(0x8B31,vs),fragment=shader(0x8B30,fs);program=glCreateProgram();glAttachShader(program,vertex);glAttachShader(program,fragment);glLinkProgram(program);GLint ok;glGetProgramiv(program,0x8B82,&ok);if(!ok){char b[1024];glGetProgramInfoLog(program,sizeof b,NULL,b);fprintf(stderr,"link: %s\n",b);return 2;}glUseProgram(program);attr=glGetAttribLocation(program,"p");uvattr=glGetAttribLocation(program,"uv");tint=glGetUniformLocation(program,"color");glUniform1i(glGetUniformLocation(program,"image"),0);glGenBuffers(1,&vbo);glEnableVertexAttribArray((GLuint)attr);glEnableVertexAttribArray((GLuint)uvattr);glEnable(0x0BE2);glBlendFunc(0x0302,0x0303);glViewport(0,0,(int)W,(int)H);
 GLuint map=texture("assets/map.rgba",1536,1024),walk[8];for(int i=0;i<8;i++){char p[80];snprintf(p,sizeof p,"assets/walk%03d.rgba",i*45);walk[i]=texture(p,1440,540);}unsigned char pixel[]={255,255,255,255};glGenTextures(1,&white);glBindTexture(TEX,white);glTexParameteri(TEX,0x2801,0x2600);glTexParameteri(TEX,0x2800,0x2600);glTexImage2D(TEX,0,0x1908,1,1,0,0x1908,0x1401,pixel);
 float px=768,py=650,tx=768,ty=650,cx=768,cy=512,zoom=1.5f,cursorx=W/2,cursory=H/2;int running=1,active=1,direction=0,frame=0;float animation=0;uint64_t last=SDL_GetPerformanceCounter(),frames=0;double elapsed=0,report=0;
 fprintf(stderr,"family-native 0.1.0: native SDL2/GLES2 Atlas ready; OK sets destination; arrows move cursor; +/- zoom; Back exits\n");
 while(running){uint64_t now=SDL_GetPerformanceCounter();float realdt=(float)((double)(now-last)/SDL_GetPerformanceFrequency());last=now;float dt=fminf(realdt,0.05f);union{uint64_t alignment;unsigned char bytes[64];}event;
  while(SDL_PollEvent(&event)){unsigned char *e=event.bytes;int type=event_int(e,0);if(type==0x100){running=0;}else if(type==0x200){int k=e[12];if(k==2||k==7||k==13)active=0;if(k==1||k==9||k==12)active=1;if(k==14)running=0;}else if(type==0x400){cursorx=clamp((float)event_int(e,20),0,W);cursory=clamp((float)event_int(e,24),0,H);}else if(type==0x401){cursorx=clamp((float)event_int(e,20),0,W);cursory=clamp((float)event_int(e,24),0,H);tx=clamp(cx+(cursorx-W/2)/zoom,0,1536);ty=clamp(cy+(cursory-H/2)/zoom,0,1024);}else if(type==0x300){int key=event_int(e,20);if(key==27||key==461||key==1073742094)running=0;else if(key==13||key==1073741912){tx=clamp(cx+(cursorx-W/2)/zoom,0,1536);ty=clamp(cy+(cursory-H/2)/zoom,0,1024);}else if(key==1073741904)cursorx=clamp(cursorx-40,20,W-20);else if(key==1073741903)cursorx=clamp(cursorx+40,20,W-20);else if(key==1073741906)cursory=clamp(cursory-40,20,H-20);else if(key==1073741905)cursory=clamp(cursory+40,20,H-20);else if(key=='+'||key=='=')zoom=clamp(zoom*1.15f,0.9f,4);else if(key=='-')zoom=clamp(zoom/1.15f,0.9f,4);}else if(type==0x403){zoom=clamp(zoom*powf(1.12f,(float)event_int(e,20)),0.9f,4);}}
  if(!active){SDL_Delay(50);continue;}
  float dx=tx-px,dy=ty-py,dist=hypotf(dx,dy);int moving=dist>0.5f;if(moving){float step=fminf(44*dt,dist);px+=dx/dist*step;py+=dy/dist*step;float angle=atan2f(dy,dx)*180/3.14159265f;if(angle<0)angle+=360;direction=((int)floorf((angle+22.5f)/45))%8;animation+=dt;frame=((int)(animation*24))%24;}else{animation=0;frame=0;}
  float blend=1-expf(-dt*3.5f);cx+=(px-cx)*blend;cy+=(py-cy)*blend;float hw=W/zoom/2,hh=H/zoom/2;cx=hw>=768?768:clamp(cx,hw,1536-hw);cy=hh>=512?512:clamp(cy,hh,1024-hh);
  glClearColor(.08f,.13f,.11f,1);glClear(0x4000);quad(map,W/2-cx*zoom,H/2-cy*zoom,1536*zoom,1024*zoom,0,0,1,1,1,1,1,1);
  float markerx=W/2+(tx-cx)*zoom,markery=H/2+(ty-cy)*zoom;quad(white,markerx-11,markery-2,22,4,0,0,1,1,1,.85f,.2f,.85f);quad(white,markerx-2,markery-11,4,22,0,0,1,1,1,.85f,.2f,.85f);
  float s=.5114155251f*zoom;quad(walk[direction],W/2+(px-cx)*zoom-119.5f*s,H/2+(py-cy)*zoom-114*s,240*s,135*s,(frame%6)/6.0f,(frame/6)/4.0f,1/6.0f,1/4.0f,1,1,1,1);
  quad(white,cursorx-9,cursory-1,18,2,0,0,1,1,1,1,1,.9f);quad(white,cursorx-1,cursory-9,2,18,0,0,1,1,1,1,1,.9f);
  SDL_GL_SwapWindow(window);frames++;elapsed+=realdt;report+=realdt;if(report>=10){fprintf(stderr,"family-native rendered=%llu active_seconds=%.1f; device timing is measured after deployment\n",(unsigned long long)frames,elapsed);report=0;}
 }
 glDeleteTextures(1,&map);glDeleteTextures(8,walk);glDeleteTextures(1,&white);glDeleteBuffers(1,&vbo);glDeleteProgram(program);glDeleteShader(vertex);glDeleteShader(fragment);SDL_GL_DeleteContext(context);SDL_DestroyWindow(window);SDL_Quit();return 0;
}
