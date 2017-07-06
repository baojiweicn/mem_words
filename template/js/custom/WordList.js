window.onload = function(){
  load_words();
};

function getURLParameter(name) {
    return decodeURIComponent((new RegExp('[?|&]' + name + '=' + '([^&;]+?)(&|#|;|$)').exec(location.search)||[,""])[1].replace(/\+/g, '%20'))||null;
};

function load_words(){
  show_wordlist();
};

function get_words(wordlist_id){
  var url = "/words/wordlists/" + wordlist_id +"/words";
  var res = $.ajax({url:url,async:false});
  return res;
};

function show_wordlist(){
  wordlist_id = getURLParameter("wordlist_id");
  document.getElementById("wordlist").dataset.wordlist = wordlist_id;
  res_name = get_wordlist_name(wordlist_id);
  if (res_name.status == 200){
    wordlist = res_name.responseJSON;
    wordlist_name = wordlist[0]["name"];
    document.getElementById("word_list").innerText = wordlist_name;
    words = wordlist[0]["words"];
    adapt_words(words);
    document.getElementById("wordlist_details").style.display = "";
    document.getElementById("details").style.display = "none";
    document.getElementById("phonetic").textContent = "";
  }
  else{
      document.getElementById("word_list").innerHTML = "请登录";
  } 
};

function show_word(word){
  set_query(word);
  document.getElementById("wordlist_details").style.display = "none";
  document.getElementById("details").style.display = "";
}

function adapt_words(words){
  radios = ""
  for(var i=0;i<words.length;i++){
    word = words[i];
    radio = "<span style=\"color:#fff\"> &nbsp"+word+"</span><br>";
    radios = radios + radio;
  }
  radio_list = document.getElementById("wordlist_details").children[0];
  radio_list.innerHTML = radios;
};

function get_wordlist_name(wordlist_id){
  var url = "/words/wordlists/" + "?id=" + wordlist_id;
  var res = $.ajax({url:url,async:false});
  return res;
};

function user_login(username){
  var url = "/words/users";
  var data = {"username":username};
  var res = $.ajax({type: 'POST',url: url,data: JSON.stringify(data),dataType: "json"});
  return res;
};

function set_query(word){
	document.getElementById("word_list").textContent = word;
  document.getElementById("pronounce").src = '/words/audios/' + word;
  var res = load_explain(word);
  var res_basic = res.responseJSON.basic;
  var res_web = res.responseJSON.web;
  set_query_phonetic(res_basic);
  set_query_explain(res_basic);
  set_query_examples(res_web);
};

function load_explain(word){
	var url = "/words/translates/" + word;
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
  document.getElementById("details").style.display = 'none';
  words_result[words[words_index]] = word_state;
  if(words_index<words.length && words.length>0){
    if(word_state == 'remember'){
      words.splice(words_index,1);
      words_index -=1;
      //check_empty();
    }
    else if (words[words_index] in words_tmp){
      if (words_tmp[words[words_index]] ==3 ){
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
  update_word(words_index);
};

function check_empty(){
  if(words.length==0){
    jqu
    console.log('finished');
  }
};

function add_wordlist_word(wordlist_id,word){
  var url = "/words/wordlists/" + wordlist_id +"/words";
  var data = {"word":word};
  var res = $.ajax({type: 'POST',url: url,data: JSON.stringify(data),dataType: "json"});
  return res;
};

document.getElementById("review_word").onclick = function(){
  window.location.href='WordListReview.html?wordlist_id='+wordlist_id;
};

document.getElementById("add_word").onclick = function(){
  document.getElementById("input_area").style.visibility = "";
};

document.getElementById("search").onclick = function(){
  word = $("#wordlist_input").val().replace(/^\s+|\s+$/g,"");
  show_word(word);
};

document.getElementById("add").onclick = function(){
  wordlist_id = document.getElementById("wordlist").dataset.wordlist;
  word = $("#wordlist_input").val().replace(/^\s+|\s+$/g,"");
  res = add_wordlist_word(wordlist_id,word);
};

document.getElementById("cancle").onclick = function(){
  document.getElementById("input_area").style.visibility = "hidden";
  show_wordlist();
};

document.getElementById("phonetic").onclick = function(){
  next_step = false;
  document.getElementById("pronounce").load();
  document.getElementById("pronounce").play();
};


