
var n = 30;
var tm = setInterval(countDown,1000);

function countDown(){
   n--;
   if(n == 0){
      // clearInterval(tm);
      n=30;
      location.reload(); 
      //get_result();
   }
   console.log(n);
}
