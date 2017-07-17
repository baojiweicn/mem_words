var words = [];
var words_index = 0;
var next_step = false;
//用于记录单词的状态
var word_state = 'not remember';
var words_result = {};
var words_tmp = {};
var wordlist_id = 0;
window.onload = function(){
  wordlist_id = getURLParameter("wordlist_id");
  document.getElementById("wordlist").dataset.wordlist = wordlist_id;
  res = get_wordlist_words(wordlist_id)
  if(res.status == 200){
      words = res.responseJSON;
      update_word(0);
  } 
  else{
      document.getElementById("query").innerHTML = "请登录";
  }   
};

function getURLParameter(name) {
    return decodeURIComponent((new RegExp('[?|&]' + name + '=' + '([^&;]+?)(&|#|;|$)').exec(location.search)||[,""])[1].replace(/\+/g, '%20'))||null;
};

function update_word(word_index){
  var word = words[word_index];
  set_query(word);  
  document.getElementById("remains").innerText = '['+words.length+']';
}

function user_login(username){
  var url = "/words/users";
  var data = {"username":username};
  var res = $.ajax({type: 'POST',url: url,data: JSON.stringify(data),dataType: "json"});
  return res;
};

function get_wordlist_words(wordlist_id){
  var url = "/words/wordlists/" + wordlist_id + "/review";
  var res = $.ajax({url:url,async:false});
  return res;
};

function set_wordlist_words(wordlist_id){
  var url = "/words/wordlists/" + wordlist_id + "/review";
  var put_data = [];
  var words_key = Object.keys(words_result);
  for(var i=0;i<words_key.length;i++){
    put_data.push({
      "word": words_key[i],
      "state": words_result[words_key[i]]
    })
  }
  $.ajax({
    url:url,
    data: JSON.stringify(put_data),
    type:'put',
    dataType:'json',
    success: function(data){
      window.location.href='/html/WordList.html?wordlist_id='+wordlist_id;
    }
  });

  //var res = $.ajax({url:url,data:})
};

function set_query(query){
  document.getElementById("query").textContent = query;
  document.getElementById("pronounce").src = '/words/audios/' + query;
  var res = load_explain(query);
  var res_basic = res.responseJSON.basic;
  var res_web = res.responseJSON.web;
  set_query_phonetic(res_basic);
  set_query_explain(res_basic);
  set_query_examples(res_web);
};

function load_explain(query){
  var url = "/words/translates/" + query;
  var res = $.ajax({url:url,async:false});
  return res;
};

function set_query_phonetic(res_basic){
  var phonetics_text = '[uk]' + res_basic['uk-phonetic'] + ' [us]' + res_basic['us-phonetic'];
  document.getElementById("phonetic").textContent = phonetics_text;
};

function set_query_explain(res_basic){
  var explain_text = '';
  var explains = res_basic.explains;
  for (var i=0;i<explains.length;i++){
    explain_text += explains[i] + '<br>';
  };
  document.getElementById("explain").innerHTML = explain_text.toString();
};

function set_query_examples(res_web){
  var examples_text = '';
  for (var i=0;i<res_web.length;i++){
    examples_text += res_web[i]['key'] + ': ' + res_web[i]['value'].join("；") + '<br>';
  };
  document.getElementById("examples").innerHTML = examples_text.toString();
};

function next_word(){
  document.getElementById("details").style.visibility = 'hidden';
  words_result[words[words_index]] = word_state;
  if(words_index<words.length && words.length>0){
    if(word_state == 'remember'){
      words.splice(words_index,1);
      words_index -=1;
      //check_empty();
    }
    else if (words[words_index] in words_tmp){
      if (words_tmp[words[words_index]] ==2 ){
        words.splice(words_index,1);
        words_index -=1;
        //check_empty();
      }
      else{
        words_tmp[words[words_index]] += 1;
      }
    }
    else {
      words_tmp[words[words_index]] = 1;
    }
    words_index +=1;
    if(words_index == words.length){
      words_index=0;
    }  
  }
  else if(words_index>=words.length){
    words_index=0;
  }
  check_empty();
};

function check_empty(){
  if(words.length==0){
    console.log('finished');
    set_wordlist_words(wordlist_id);
  }
  else{
    update_word(words_index);
  }
};
document.getElementById("phonetic").onclick = function(){
  next_step = false;
  document.getElementById("pronounce").load();
  document.getElementById("pronounce").play();
};


document.getElementById("query").onclick = function(){
  next_step = false;
  document.getElementById("details").style.visibility = '';
  document.getElementById("pronounce").load();
  document.getElementById("pronounce").play();
};

document.getElementById("nonrecognition").onclick = function(){
  next_step = true;
  word_state = 'not remember';
  document.getElementById("details").style.visibility = '';
  document.getElementById("pronounce").load();
  document.getElementById("pronounce").play();
};

document.getElementById("confusion").onclick = function(){
  next_step = true;
  word_state = 'confuse';
  document.getElementById("details").style.visibility = '';
  document.getElementById("pronounce").load();
  document.getElementById("pronounce").play();
};

document.getElementById("recognition").onclick = function(){
  next_step = true;
  word_state = 'remember';
  document.getElementById("details").style.visibility = '';
  document.getElementById("pronounce").load();
  document.getElementById("pronounce").play();
};

document.getElementById("pronounce").onended = function(){
  if(next_step){
    next_word();
  }
};

